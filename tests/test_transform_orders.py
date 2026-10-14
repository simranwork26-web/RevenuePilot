import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src import transform_orders


class TestBuildOrdersAnalytics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.raw_dir = Path(self.temp_dir.name)
        transform_orders.RAW_DATA_DIR = self.raw_dir

        pd.DataFrame([
            {
                "order_id": "order_1",
                "customer_id": "customer_1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-01 10:00:00",
            },
            {
                "order_id": "order_2",
                "customer_id": "customer_2",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-01-02 11:00:00",
            },
        ]).to_csv(
            self.raw_dir / "olist_orders_dataset.csv", index=False
        )

        pd.DataFrame([
            {"customer_id": "customer_1", "customer_unique_id": "unique_1"},
            {"customer_id": "customer_2", "customer_unique_id": "unique_2"},
        ]).to_csv(
            self.raw_dir / "olist_customers_dataset.csv", index=False
        )

        pd.DataFrame([
            {"order_id": "order_1", "price": 100.0, "freight_value": 10.0},
            {"order_id": "order_1", "price": 50.0, "freight_value": 5.0},
        ]).to_csv(
            self.raw_dir / "olist_order_items_dataset.csv", index=False
        )

        pd.DataFrame([
            {"order_id": "order_1", "payment_value": 60.0},
            {"order_id": "order_1", "payment_value": 105.0},
        ]).to_csv(
            self.raw_dir / "olist_order_payments_dataset.csv", index=False
        )

        pd.DataFrame([
            {"order_id": "order_1", "review_score": 5},
            {"order_id": "order_1", "review_score": 3},
        ]).to_csv(
            self.raw_dir / "olist_order_reviews_dataset.csv", index=False
        )

    def test_aggregates_without_join_fanout(self):
        result = transform_orders.build_orders_analytics()

        self.assertEqual(len(result), 2)
        self.assertEqual(result["order_id"].nunique(), 2)
        self.assertEqual(result["order_id"].duplicated().sum(), 0)

        order = result.set_index("order_id").loc["order_1"]

        self.assertEqual(order["item_count"], 2)
        self.assertAlmostEqual(order["item_value"], 150.0)
        self.assertAlmostEqual(order["freight_value"], 15.0)
        self.assertAlmostEqual(order["payment_value"], 165.0)
        self.assertAlmostEqual(order["review_score"], 4.0)

    def test_preserves_orders_without_child_records(self):
        result = transform_orders.build_orders_analytics()
        order = result.set_index("order_id").loc["order_2"]

        self.assertTrue(pd.isna(order["item_count"]))
        self.assertTrue(pd.isna(order["item_value"]))
        self.assertTrue(pd.isna(order["freight_value"]))
        self.assertTrue(pd.isna(order["payment_value"]))
        self.assertTrue(pd.isna(order["review_score"]))


    def test_aggregated_totals_match_source_tables(self):
        result = transform_orders.build_orders_analytics()

        items = pd.read_csv(
            self.raw_dir / "olist_order_items_dataset.csv"
        )
        payments = pd.read_csv(
            self.raw_dir / "olist_order_payments_dataset.csv"
        )

        self.assertEqual(int(result["item_count"].sum()), len(items))
        self.assertAlmostEqual(
            result["item_value"].sum(), items["price"].sum()
        )
        self.assertAlmostEqual(
            result["freight_value"].sum(), items["freight_value"].sum()
        )
        self.assertAlmostEqual(
            result["payment_value"].sum(), payments["payment_value"].sum()
        )


if __name__ == "__main__":
    unittest.main()
