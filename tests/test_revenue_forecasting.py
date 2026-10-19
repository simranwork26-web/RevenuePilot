import unittest

import numpy as np
import pandas as pd

from src.revenue_forecasting import (
    evaluate_expanding_window,
    evaluate_forecast,
    evaluate_linear_trend,
    forecast_linear_trend,
    forecast_damped_trend,
    forecast_seasonal_naive,
    prepare_weekly_revenue,
)


class TestRevenueForecasting(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({
            "week_start": pd.date_range(
                "2024-01-01", periods=16, freq="7D"
            ),
            "delivered_revenue": [
                100, 110, 120, 130, 140, 150, 160, 170,
                180, 190, 200, 210, 220, 230, 240, 250,
            ],
        })

    def test_forecast_returns_requested_number_of_weeks(self):
        result = forecast_linear_trend(self.data.iloc[:12], horizon=4)

        self.assertEqual(len(result), 4)
        self.assertEqual(
            result["week_start"].tolist(),
            pd.date_range("2024-03-25", periods=4, freq="7D").tolist(),
        )

    def test_linear_trend_recovers_simple_increasing_series(self):
        result = forecast_linear_trend(self.data.iloc[:12], horizon=2)

        np.testing.assert_allclose(
            result["forecast_revenue"].to_numpy(),
            [220.0, 230.0],
            atol=1e-8,
        )

    def test_damped_trend_factor_one_matches_linear_trend(self):
        linear = forecast_linear_trend(self.data.iloc[:12], horizon=4)
        damped = forecast_damped_trend(
            self.data.iloc[:12], horizon=4, damping_factor=1.0
        )

        np.testing.assert_allclose(
            damped["forecast_revenue"].to_numpy(),
            linear["forecast_revenue"].to_numpy(),
            rtol=1e-10,
            atol=1e-8,
        )

    def test_damped_trend_factor_zero_is_flat_at_origin(self):
        training = self.data.iloc[:12]
        result = forecast_damped_trend(
            training, horizon=4, damping_factor=0.0
        )

        np.testing.assert_allclose(
            result["forecast_revenue"].to_numpy(),
            np.full(4, 210.0),
            atol=1e-8,
        )

    def test_damped_trend_rejects_invalid_damping_factor(self):
        for factor in (-0.1, 1.1, float("nan"), float("inf"), True):
            with self.subTest(factor=factor):
                with self.assertRaisesRegex(
                    ValueError, "damping_factor must be"
                ):
                    forecast_damped_trend(
                        self.data.iloc[:12], damping_factor=factor
                    )

    def test_evaluate_forecast_metrics(self):
        metrics = evaluate_forecast(
            pd.Series([100.0, 200.0]),
            pd.Series([90.0, 220.0]),
        )

        self.assertAlmostEqual(metrics["mae"], 15.0)
        self.assertAlmostEqual(
            metrics["rmse"], np.sqrt(250.0), places=8
        )
        self.assertAlmostEqual(metrics["wape_pct"], 10.0)

    def test_rejects_missing_columns(self):
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            prepare_weekly_revenue(pd.DataFrame({"week_start": ["2024-01-01"]}))

    def test_rejects_duplicate_weeks(self):
        duplicated = pd.concat(
            [self.data.iloc[:3], self.data.iloc[[2]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "week_start must be unique"):
            prepare_weekly_revenue(duplicated)

    def test_rejects_gaps_in_weekly_series(self):
        gapped = self.data.drop(index=2).reset_index(drop=True)

        with self.assertRaisesRegex(ValueError, "exactly seven days apart"):
            prepare_weekly_revenue(gapped)

    def test_rejects_negative_revenue(self):
        invalid = self.data.copy()
        invalid.loc[0, "delivered_revenue"] = -1

        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            prepare_weekly_revenue(invalid)

    def test_holdout_evaluation_uses_chronological_split(self):
        result = evaluate_linear_trend(self.data, test_weeks=4)

        self.assertEqual(result["training_weeks"], 12)
        self.assertEqual(result["test_weeks"], 4)
        self.assertEqual(result["training_end"], "2024-03-18")
        self.assertEqual(result["test_start"], "2024-03-25")
        self.assertEqual(result["test_end"], "2024-04-15")
        self.assertLess(
            result["linear_trend"]["mae"],
            result["baseline"]["mae"],
        )


    def test_seasonal_naive_uses_values_from_52_weeks_earlier(self):
        data = pd.DataFrame({
            "week_start": pd.date_range("2023-01-02", periods=60, freq="7D"),
            "delivered_revenue": np.arange(60, dtype=float) * 100.0,
        })

        result = forecast_seasonal_naive(data, horizon=4)

        np.testing.assert_allclose(
            result["forecast_revenue"].to_numpy(),
            data["delivered_revenue"].iloc[8:12].to_numpy(),
        )
        self.assertEqual(
            result["week_start"].tolist(),
            pd.date_range("2024-02-26", periods=4, freq="7D").tolist(),
        )

    def test_seasonal_naive_rejects_insufficient_history(self):
        with self.assertRaisesRegex(ValueError, "At least 52 observations"):
            forecast_seasonal_naive(self.data, horizon=4)

    def test_holdout_includes_seasonal_naive_when_history_is_sufficient(self):
        data = pd.DataFrame({
            "week_start": pd.date_range("2023-01-02", periods=64, freq="7D"),
            "delivered_revenue": np.arange(64, dtype=float) * 100.0 + 1000.0,
        })

        result = evaluate_linear_trend(data, test_weeks=4)

        self.assertIn("seasonal_naive", result)
        self.assertEqual(result["training_weeks"], 60)
        self.assertEqual(result["test_weeks"], 4)
        self.assertGreaterEqual(result["seasonal_naive"]["wape_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()


class TestExpandingWindowEvaluation(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({
            "week_start": pd.date_range(
                "2024-01-01", periods=24, freq="7D"
            ),
            "delivered_revenue": np.arange(24, dtype=float) * 10 + 100,
        })

    def test_expanding_windows_grow_and_test_periods_do_not_overlap(self):
        result = evaluate_expanding_window(
            self.data,
            horizon=4,
            initial_train_weeks=8,
            step_size=4,
        )

        self.assertEqual(result["fold_count"], 4)
        self.assertEqual(result["evaluated_weeks"], 16)
        self.assertEqual(
            [fold["training_weeks"] for fold in result["folds"]],
            [8, 12, 16, 20],
        )
        self.assertEqual(result["folds"][0]["test_start"], "2024-02-26")
        self.assertEqual(result["folds"][-1]["test_end"], "2024-06-10")

    def test_aggregate_metrics_include_expected_models(self):
        result = evaluate_expanding_window(
            self.data,
            horizon=4,
            initial_train_weeks=8,
            step_size=4,
        )

        metrics = result["aggregate_metrics"]
        self.assertEqual(
            set(metrics),
            {
                "linear_trend",
                "damped_trend_0.25",
                "baseline",
                "4_week_average",
                "8_week_average",
            },
        )
        for model_metrics in metrics.values():
            self.assertIn("mae", model_metrics)
            self.assertIn("rmse", model_metrics)
            self.assertIn("wape_pct", model_metrics)

    def test_future_revenue_does_not_change_earlier_fold_predictions(self):
        original = evaluate_expanding_window(
            self.data,
            horizon=4,
            initial_train_weeks=8,
            step_size=4,
        )

        changed_data = self.data.copy()
        changed_data.loc[12:, "delivered_revenue"] += 100_000
        changed = evaluate_expanding_window(
            changed_data,
            horizon=4,
            initial_train_weeks=8,
            step_size=4,
        )

        original_first = original["folds"][0]["models"]
        changed_first = changed["folds"][0]["models"]
        self.assertEqual(original_first, changed_first)

    def test_rejects_insufficient_observations(self):
        with self.assertRaisesRegex(ValueError, "Insufficient observations"):
            evaluate_expanding_window(
                self.data.iloc[:10],
                horizon=4,
                initial_train_weeks=8,
                step_size=4,
            )

    def test_rejects_invalid_parameters(self):
        for kwargs, message in (
            ({"horizon": 0}, "horizon must be a positive integer"),
            ({"initial_train_weeks": 2}, "initial_train_weeks must be"),
            ({"step_size": 0}, "step_size must be a positive integer"),
            ({"horizon": True}, "horizon must be a positive integer"),
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_expanding_window(self.data, **kwargs)
