import unittest

import pandas as pd

from src.monthly_analytics import (
    LOW_VOLUME_THRESHOLD,
    build_monthly_analytics,
)


class TestMonthlyAnalytics(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "order_1",
                "order_purchase_timestamp": "2018-01-05 10:00:00",
                "order_status": "delivered",
                "item_value": 100.0,
                "payment_value": 110.0,
            },
            {
                "order_id": "order_2",
                "order_purchase_timestamp": "2018-01-20 12:00:00",
                "order_status": "canceled",
                "item_value": 50.0,
                "payment_value": 55.0,
            },
            {
                "order_id": "order_3",
                "order_purchase_timestamp": "2018-03-02 09:00:00",
                "order_status": "delivered",
                "item_value": 80.0,
                "payment_value": 90.0,
            },
        ])

    def test_aggregates_monthly_metrics(self):
        result = build_monthly_analytics(self.orders)
        january = result.set_index("month").loc[pd.Timestamp("2018-01-01")]

        self.assertEqual(january["order_count"], 2)
        self.assertEqual(january["delivered_order_count"], 1)
        self.assertAlmostEqual(january["item_value_total"], 150.0)
        self.assertAlmostEqual(january["delivered_item_value"], 100.0)
        self.assertAlmostEqual(
            january["recorded_payment_value_total"], 165.0
        )

    def test_inserts_missing_calendar_month(self):
        result = build_monthly_analytics(self.orders)
        february = result.set_index("month").loc[pd.Timestamp("2018-02-01")]

        self.assertEqual(len(result), 3)
        self.assertEqual(february["order_count"], 0)
        self.assertEqual(february["delivered_order_count"], 0)
        self.assertEqual(february["item_value_total"], 0.0)
        self.assertEqual(february["delivered_item_value"], 0.0)
        self.assertEqual(february["recorded_payment_value_total"], 0.0)

    def test_flags_low_volume_months(self):
        result = build_monthly_analytics(self.orders)

        self.assertTrue(result["low_volume_month"].all())
        self.assertEqual(LOW_VOLUME_THRESHOLD, 100)

    def test_rejects_duplicate_order_ids(self):
        duplicated = pd.concat(
            [self.orders, self.orders.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "order_id must be unique"):
            build_monthly_analytics(duplicated)

    def test_rejects_missing_required_columns(self):
        incomplete = self.orders.drop(columns=["payment_value"])

        with self.assertRaisesRegex(ValueError, "payment_value"):
            build_monthly_analytics(incomplete)


if __name__ == "__main__":
    unittest.main()
