import unittest
from unittest.mock import patch

import pandas as pd

from backend.analytics import get_revenue_forecast


class TestForecastEndpoint(unittest.TestCase):

    @patch("backend.analytics.forecast_damped_trend")
    @patch("backend.analytics.evaluate_damped_trend")
    @patch("backend.analytics.load_weekly_revenue")
    def test_forecast_response_contract(
        self,
        mock_load,
        mock_evaluate,
        mock_forecast,
    ):
        mock_load.return_value = pd.DataFrame({
            "week_start": pd.to_datetime([
                "2018-08-13",
                "2018-08-20",
            ]),
            "revenue": [1000.0, 1200.0],
        })

        mock_evaluate.return_value = {
            "mae": 100.0,
            "rmse": 125.0,
            "wape": 10.0,
        }

        mock_forecast.return_value = pd.DataFrame({
            "week_start": pd.to_datetime([
                "2018-08-27",
                "2018-09-03",
                "2018-09-10",
                "2018-09-17",
            ]),
            "forecast_revenue": [
                1300.123,
                1400.456,
                1500.789,
                1600.111,
            ],
        })

        response = get_revenue_forecast()

        self.assertEqual(
            response["forecast_horizon_weeks"], 4
        )
        self.assertEqual(
            response["revenue_metric"],
            "delivered_item_revenue",
        )
        self.assertEqual(response["currency"], "BRL")
        self.assertEqual(
            response["historical_cutoff"],
            "2018-08-20T00:00:00",
        )
        self.assertEqual(
            response["forecast_status"],
            "historical_demo",
        )

        self.assertEqual(len(response["forecast"]), 4)

        self.assertEqual(
            response["forecast"][0],
            {
                "week_start": "2018-08-27T00:00:00",
                "forecast_revenue": 1300.12,
            },
        )

        self.assertEqual(
            response["evaluation"],
            mock_evaluate.return_value,
        )

        mock_evaluate.assert_called_once()
        self.assertEqual(
            mock_evaluate.call_args.kwargs["test_weeks"],
            12,
        )
        self.assertEqual(
            mock_evaluate.call_args.kwargs["damping_factor"],
            0.25,
        )

        mock_forecast.assert_called_once()
        self.assertEqual(
            mock_forecast.call_args.kwargs["horizon"],
            4,
        )
        self.assertEqual(
            mock_forecast.call_args.kwargs["damping_factor"],
            0.25,
        )


if __name__ == "__main__":
    unittest.main()
