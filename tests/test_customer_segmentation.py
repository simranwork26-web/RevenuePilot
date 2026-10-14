import unittest

import pandas as pd

from src.customer_segmentation import build_customer_segmentation


class TestCustomerSegmentation(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "o1",
                "customer_unique_id": "repeat_high",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-01",
                "item_value": 300.0,
                "payment_value": 320.0,
            },
            {
                "order_id": "o2",
                "customer_unique_id": "repeat_high",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-06-01",
                "item_value": 250.0,
                "payment_value": 270.0,
            },
            {
                "order_id": "o3",
                "customer_unique_id": "repeat_regular",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-03-01",
                "item_value": 200.0,
                "payment_value": 220.0,
            },
            {
                "order_id": "o4",
                "customer_unique_id": "repeat_regular",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-04-01",
                "item_value": 50.0,
                "payment_value": 50.0,
            },
            {
                "order_id": "o5",
                "customer_unique_id": "one_time",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-07-01",
                "item_value": 80.0,
                "payment_value": 90.0,
            },
            {
                "order_id": "o6",
                "customer_unique_id": "no_delivery",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-08-01",
                "item_value": 60.0,
                "payment_value": 60.0,
            },
        ])
        self.reference_date = pd.Timestamp("2018-09-01")

    def test_assigns_expected_customer_segments(self):
        result = build_customer_segmentation(
            self.orders, self.reference_date
        ).set_index("customer_unique_id")

        self.assertEqual(result.loc["repeat_high", "segment"], "High-value repeat")
        self.assertEqual(result.loc["repeat_regular", "segment"], "Repeat")
        self.assertEqual(result.loc["one_time", "segment"], "One-time")
        self.assertEqual(result.loc["no_delivery", "segment"], "No delivered order")

    def test_aggregates_customer_metrics(self):
        result = build_customer_segmentation(
            self.orders, self.reference_date
        ).set_index("customer_unique_id")

        self.assertEqual(result.loc["repeat_high", "order_count"], 2)
        self.assertEqual(result.loc["repeat_high", "delivered_order_count"], 2)
        self.assertAlmostEqual(
            result.loc["repeat_high", "delivered_item_value"], 550.0
        )
        self.assertAlmostEqual(
            result.loc["repeat_high", "delivered_payment_value"], 590.0
        )
        self.assertEqual(result.loc["repeat_high", "recency_days"], 92)

    def test_preserves_all_customers(self):
        result = build_customer_segmentation(
            self.orders, self.reference_date
        )

        self.assertEqual(len(result), 4)
        self.assertEqual(result["customer_unique_id"].nunique(), 4)

    def test_uses_fixed_reference_date(self):
        result = build_customer_segmentation(
            self.orders, self.reference_date
        )

        self.assertTrue(
            (result["reference_date"] == pd.Timestamp("2018-09-01")).all()
        )

    def test_rejects_duplicate_order_ids(self):
        duplicated = pd.concat(
            [self.orders, self.orders.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "order_id"):
            build_customer_segmentation(duplicated, self.reference_date)

    def test_rejects_missing_required_columns(self):
        incomplete = self.orders.drop(columns=["payment_value"])

        with self.assertRaisesRegex(ValueError, "payment_value"):
            build_customer_segmentation(incomplete, self.reference_date)

    def test_rejects_reference_date_before_latest_purchase(self):
        with self.assertRaisesRegex(ValueError, "cannot precede"):
            build_customer_segmentation(
                self.orders, pd.Timestamp("2018-07-31")
            )


if __name__ == "__main__":
    unittest.main()
