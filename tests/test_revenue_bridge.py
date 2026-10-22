import unittest

from backend.revenue_bridge import build_revenue_bridge


class TestRevenueBridge(unittest.TestCase):

    def test_decomposes_revenue_change_into_volume_and_value(self):
        previous = {
            "month": "2018-01-01",
            "delivered_order_count": 10,
            "delivered_item_value": 1000.0,
        }
        current = {
            "month": "2018-02-01",
            "delivered_order_count": 12,
            "delivered_item_value": 1500.0,
        }

        result = build_revenue_bridge(previous, current)

        self.assertEqual(result["revenue_change"], 500.0)
        self.assertEqual(result["revenue_change_pct"], 50.0)
        self.assertAlmostEqual(
            result["volume_impact"] + result["average_order_value_impact"],
            result["revenue_change"],
        )

    def test_handles_no_revenue_change(self):
        month = {
            "month": "2018-01-01",
            "delivered_order_count": 10,
            "delivered_item_value": 1000.0,
        }

        result = build_revenue_bridge(month, month)

        self.assertEqual(result["revenue_change"], 0.0)
        self.assertEqual(result["revenue_change_pct"], 0.0)
        self.assertEqual(result["volume_impact"], 0.0)
        self.assertEqual(result["average_order_value_impact"], 0.0)

    def test_volume_and_order_value_impacts_offset_correctly(self):
        previous = {
            "month": "2018-01-01",
            "delivered_order_count": 10,
            "delivered_item_value": 1000.0,
        }
        current = {
            "month": "2018-02-01",
            "delivered_order_count": 8,
            "delivered_item_value": 1200.0,
        }

        result = build_revenue_bridge(previous, current)

        self.assertEqual(result["revenue_change"], 200.0)
        self.assertAlmostEqual(result["volume_impact"], -250.0)
        self.assertAlmostEqual(result["average_order_value_impact"], 450.0)
        self.assertAlmostEqual(
            result["volume_impact"] + result["average_order_value_impact"],
            result["revenue_change"],
        )

    def test_handles_zero_previous_revenue(self):
        previous = {
            "month": "2018-01-01",
            "delivered_order_count": 0,
            "delivered_item_value": 0.0,
        }
        current = {
            "month": "2018-02-01",
            "delivered_order_count": 5,
            "delivered_item_value": 500.0,
        }

        result = build_revenue_bridge(previous, current)

        self.assertEqual(result["revenue_change"], 500.0)
        self.assertIsNone(result["revenue_change_pct"])
        self.assertEqual(result["volume_impact"] + result["average_order_value_impact"], 500.0)


if __name__ == "__main__":
    unittest.main()
