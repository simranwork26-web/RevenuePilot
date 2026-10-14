import unittest

import pandas as pd

from src.revenue_analytics import calculate_revenue_metrics


class TestRevenueAnalytics(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "order_1",
                "customer_unique_id": "customer_a",
                "order_status": "delivered",
                "item_value": 100.0,
                "freight_value": 10.0,
                "payment_value": 110.0,
            },
            {
                "order_id": "order_2",
                "customer_unique_id": "customer_a",
                "order_status": "delivered",
                "item_value": 50.0,
                "freight_value": 5.0,
                "payment_value": 55.0,
            },
            {
                "order_id": "order_3",
                "customer_unique_id": "customer_b",
                "order_status": "canceled",
                "item_value": 20.0,
                "freight_value": 2.0,
                "payment_value": 25.0,
            },
            {
                "order_id": "order_4",
                "customer_unique_id": "customer_c",
                "order_status": "created",
                "item_value": None,
                "freight_value": None,
                "payment_value": None,
            },
        ])

    def test_calculates_core_metrics(self):
        metrics = calculate_revenue_metrics(self.orders)

        self.assertEqual(metrics["order_count"], 4)
        self.assertEqual(metrics["delivered_order_count"], 2)
        self.assertAlmostEqual(metrics["item_value_total"], 170.0)
        self.assertAlmostEqual(metrics["delivered_item_value"], 150.0)
        self.assertAlmostEqual(metrics["freight_value_total"], 17.0)
        self.assertAlmostEqual(
            metrics["recorded_payment_value_total"], 190.0
        )

    def test_averages_use_only_orders_with_records(self):
        metrics = calculate_revenue_metrics(self.orders)

        self.assertEqual(metrics["item_order_count"], 3)
        self.assertAlmostEqual(
            metrics["average_item_value_per_order"], 170.0 / 3
        )
        self.assertEqual(metrics["payment_order_count"], 3)
        self.assertAlmostEqual(
            metrics["average_recorded_payment_per_order"], 190.0 / 3
        )

    def test_counts_repeat_customers_by_unique_customer_id(self):
        metrics = calculate_revenue_metrics(self.orders)

        self.assertEqual(metrics["repeat_customer_count"], 1)
        self.assertEqual(
            metrics["repeat_customer_status_population"],
            "all order statuses",
        )

    def test_rejects_duplicate_order_ids(self):
        duplicated = pd.concat(
            [self.orders, self.orders.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "order_id must be unique"):
            calculate_revenue_metrics(duplicated)

    def test_rejects_missing_required_columns(self):
        incomplete = self.orders.drop(columns=["payment_value"])

        with self.assertRaisesRegex(ValueError, "payment_value"):
            calculate_revenue_metrics(incomplete)


if __name__ == "__main__":
    unittest.main()
