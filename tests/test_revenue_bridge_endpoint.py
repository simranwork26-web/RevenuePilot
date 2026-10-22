import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.analytics import get_revenue_bridge


class TestRevenueBridgeEndpoint(unittest.TestCase):

    @patch("backend.analytics.fetch_all")
    def test_valid_months_return_revenue_bridge(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "month": __import__("datetime").date(2018, 7, 1),
                "delivered_order_count": 6159,
                "delivered_item_value": 867953.46,
            },
            {
                "month": __import__("datetime").date(2018, 8, 1),
                "delivered_order_count": 6351,
                "delivered_item_value": 838576.64,
            },
        ]

        result = get_revenue_bridge(
            previous_month="2018-07",
            current_month="2018-08",
        )

        self.assertEqual(result["revenue_change"], -29376.82)
        self.assertEqual(result["revenue_change_pct"], -3.38)
        self.assertAlmostEqual(
            result["volume_impact"] + result["average_order_value_impact"],
            result["revenue_change"],
            places=2,
        )

        mock_fetch.assert_called_once()
        self.assertEqual(
            mock_fetch.call_args.args[1],
            (
                __import__("datetime").date(2018, 7, 1),
                __import__("datetime").date(2018, 8, 1),
            ),
        )

    def test_invalid_month_format_returns_400(self):
        with self.assertRaises(HTTPException) as context:
            get_revenue_bridge(
                previous_month="2018-7",
                current_month="2018-08",
            )

        self.assertEqual(context.exception.status_code, 400)

    def test_reversed_months_return_400(self):
        with self.assertRaises(HTTPException) as context:
            get_revenue_bridge(
                previous_month="2018-08",
                current_month="2018-07",
            )

        self.assertEqual(context.exception.status_code, 400)

    @patch("backend.analytics.fetch_all", return_value=[])
    def test_missing_month_returns_404(self, mock_fetch):
        with self.assertRaises(HTTPException) as context:
            get_revenue_bridge(
                previous_month="2018-07",
                current_month="2018-08",
            )

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
