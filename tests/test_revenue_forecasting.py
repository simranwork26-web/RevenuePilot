import unittest

import numpy as np
import pandas as pd

from src.revenue_forecasting import (
    evaluate_forecast,
    evaluate_linear_trend,
    forecast_linear_trend,
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


if __name__ == "__main__":
    unittest.main()
