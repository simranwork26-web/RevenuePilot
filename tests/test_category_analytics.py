import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src import category_analytics


class TestCategoryAnalytics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.raw_dir = Path(self.temp_dir.name)
        self.original_raw_dir = category_analytics.RAW_DATA_DIR
        category_analytics.RAW_DATA_DIR = self.raw_dir
        self.addCleanup(
            setattr,
            category_analytics,
            "RAW_DATA_DIR",
            self.original_raw_dir,
        )

        pd.DataFrame([
            {"order_id": "order_1", "order_status": "delivered"},
            {"order_id": "order_2", "order_status": "canceled"},
        ]).to_csv(
            self.raw_dir / "olist_orders_dataset.csv", index=False
        )

        pd.DataFrame([
            {
                "order_id": "order_1",
                "order_item_id": 1,
                "product_id": "product_1",
                "price": 100.0,
            },
            {
                "order_id": "order_1",
                "order_item_id": 2,
                "product_id": "product_2",
                "price": 50.0,
            },
            {
                "order_id": "order_2",
                "order_item_id": 1,
                "product_id": "missing_product",
                "price": 20.0,
            },
            {
                "order_id": "order_2",
                "order_item_id": 2,
                "product_id": "product_1",
                "price": 10.0,
            },
        ]).to_csv(
            self.raw_dir / "olist_order_items_dataset.csv", index=False
        )

        pd.DataFrame([
            {
                "product_id": "product_1",
                "product_category_name": "cat_a",
            },
            {
                "product_id": "product_2",
                "product_category_name": "pc_gamer",
            },
        ]).to_csv(
            self.raw_dir / "olist_products_dataset.csv", index=False
        )

        pd.DataFrame([
            {
                "product_category_name": "cat_a",
                "product_category_name_english": "category_a_en",
            },
        ]).to_csv(
            self.raw_dir / "product_category_name_translation.csv",
            index=False,
        )

    def test_aggregates_metrics_without_join_fanout(self):
        result = category_analytics.build_category_analytics()
        categories = result.set_index("category")

        self.assertEqual(int(result["item_count"].sum()), 4)
        self.assertEqual(int(categories.loc["category_a_en", "item_count"]), 2)
        self.assertEqual(int(categories.loc["category_a_en", "order_count"]), 2)
        self.assertEqual(
            int(categories.loc["category_a_en", "delivered_item_count"]), 1
        )
        self.assertEqual(
            int(categories.loc["category_a_en", "delivered_order_count"]), 1
        )
        self.assertAlmostEqual(
            categories.loc["category_a_en", "item_value_total"], 110.0
        )
        self.assertAlmostEqual(
            categories.loc["category_a_en", "delivered_item_value"], 100.0
        )

    def test_preserves_untranslated_and_unknown_categories(self):
        result = category_analytics.build_category_analytics()
        categories = result.set_index("category")

        self.assertIn("pc_gamer", categories.index)
        self.assertIn("unknown_category", categories.index)
        self.assertEqual(
            int(categories.loc["pc_gamer", "item_count"]), 1
        )
        self.assertEqual(
            int(categories.loc["unknown_category", "item_count"]), 1
        )
        self.assertAlmostEqual(
            categories.loc["unknown_category", "item_value_total"], 20.0
        )

    def test_category_totals_reconcile_with_source_items(self):
        result = category_analytics.build_category_analytics()
        items = pd.read_csv(
            self.raw_dir / "olist_order_items_dataset.csv"
        )

        self.assertEqual(int(result["item_count"].sum()), len(items))
        self.assertAlmostEqual(
            result["item_value_total"].sum(), items["price"].sum()
        )
        self.assertAlmostEqual(
            result["delivered_item_value"].sum(), 150.0
        )

    def test_rejects_duplicate_product_ids(self):
        products_path = self.raw_dir / "olist_products_dataset.csv"
        products = pd.read_csv(products_path)
        products = pd.concat(
            [products, products.iloc[[0]]], ignore_index=True
        )
        products.to_csv(products_path, index=False)

        with self.assertRaisesRegex(ValueError, "unique"):
            category_analytics.build_category_analytics()

    def test_rejects_duplicate_order_item_ids(self):
        items_path = self.raw_dir / "olist_order_items_dataset.csv"
        items = pd.read_csv(items_path)
        items = pd.concat(
            [items, items.iloc[[0]]], ignore_index=True
        )
        items.to_csv(items_path, index=False)

        with self.assertRaisesRegex(ValueError, "unique"):
            category_analytics.build_category_analytics()

    def test_rejects_order_items_without_matching_orders(self):
        items_path = self.raw_dir / "olist_order_items_dataset.csv"
        items = pd.read_csv(items_path)
        items.loc[0, "order_id"] = "missing_order"
        items.to_csv(items_path, index=False)

        with self.assertRaisesRegex(ValueError, "do not match"):
            category_analytics.build_category_analytics()


if __name__ == "__main__":
    unittest.main()
