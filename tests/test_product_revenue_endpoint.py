import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.analytics import get_product_revenue_diagnosis


class TestProductRevenueEndpoint(unittest.TestCase):

    @patch("backend.analytics.load_product_revenue_diagnosis")
    def test_valid_months_return_product_diagnosis(self, mock_load):
        mock_load.return_value = {
            "previous_month": "2018-07",
            "current_month": "2018-08",
            "previous_revenue": 100.0,
            "current_revenue": 80.0,
            "revenue_change": -20.0,
            "product_count": 2,
            "product_drivers": [],
            "category_drivers": [],
        }

        result = get_product_revenue_diagnosis(
            previous_month="2018-07",
            current_month="2018-08",
        )

        self.assertEqual(result["revenue_change"], -20.0)
        self.assertEqual(result["product_count"], 2)
        mock_load.assert_called_once_with("2018-07", "2018-08")

    @patch("backend.analytics.load_product_revenue_diagnosis")
    def test_invalid_month_format_returns_400(self, mock_load):
        mock_load.side_effect = ValueError(
            "previous_month must use YYYY-MM format."
        )

        with self.assertRaises(HTTPException) as context:
            get_product_revenue_diagnosis(
                previous_month="2018-7",
                current_month="2018-08",
            )

        self.assertEqual(context.exception.status_code, 400)

    @patch("backend.analytics.load_product_revenue_diagnosis")
    def test_reversed_months_return_400(self, mock_load):
        mock_load.side_effect = ValueError(
            "current_month must be later than previous_month."
        )

        with self.assertRaises(HTTPException) as context:
            get_product_revenue_diagnosis(
                previous_month="2018-08",
                current_month="2018-07",
            )

        self.assertEqual(context.exception.status_code, 400)

    @patch("backend.analytics.load_product_revenue_diagnosis")
    def test_missing_month_returns_404(self, mock_load):
        mock_load.side_effect = ValueError(
            "One or both selected months are unavailable."
        )

        with self.assertRaises(HTTPException) as context:
            get_product_revenue_diagnosis(
                previous_month="2018-07",
                current_month="2018-08",
            )

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
