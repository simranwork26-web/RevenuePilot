import unittest

import pandas as pd

from src.product_revenue_diagnosis import (
    build_product_revenue_diagnosis,
)


class TestProductRevenueDiagnosis(unittest.TestCase):

    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "o1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-07-10",
            },
            {
                "order_id": "o2",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-08-10",
            },
            {
                "order_id": "o3",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-08-15",
            },
        ])

        self.items = pd.DataFrame([
            {
                "order_id": "o1",
                "order_item_id": 1,
                "product_id": "p1",
                "price": 100.0,
            },
            {
                "order_id": "o2",
                "order_item_id": 1,
                "product_id": "p1",
                "price": 60.0,
            },
            {
                "order_id": "o2",
                "order_item_id": 2,
                "product_id": "p2",
                "price": 40.0,
            },
            {
                "order_id": "o3",
                "order_item_id": 1,
                "product_id": "p2",
                "price": 500.0,
            },
        ])

        self.products = pd.DataFrame([
            {
                "product_id": "p1",
                "product_category_name": "electronics",
            },
            {
                "product_id": "p2",
                "product_category_name": "books",
            },
        ])

        self.translations = pd.DataFrame([
            {
                "product_category_name": "electronics",
                "product_category_name_english": "electronics",
            },
            {
                "product_category_name": "books",
                "product_category_name_english": "books",
            },
        ])

    def build(self, previous="2018-07", current="2018-08"):
        return build_product_revenue_diagnosis(
            previous,
            current,
            self.orders,
            self.items,
            self.products,
            self.translations,
        )

    def test_product_revenue_changes_are_calculated(self):
        result = self.build()

        self.assertEqual(result["previous_revenue"], 100.0)
        self.assertEqual(result["current_revenue"], 100.0)
        self.assertEqual(result["revenue_change"], 0.0)

        products = {
            item["product_id"]: item
            for item in result["product_drivers"]
        }

        self.assertEqual(products["p1"]["revenue_change"], -40.0)
        self.assertEqual(products["p2"]["revenue_change"], 40.0)

    def test_non_delivered_orders_are_excluded(self):
        result = self.build()

        self.assertEqual(result["current_revenue"], 100.0)

    def test_product_changes_reconcile_to_total_change(self):
        result = self.build()

        product_change = sum(
            item["revenue_change"]
            for item in result["product_drivers"]
        )

        self.assertAlmostEqual(
            product_change,
            result["revenue_change"],
            places=2,
        )

    def test_invalid_month_format_is_rejected(self):
        with self.assertRaises(ValueError):
            self.build(previous="July 2018")

    def test_current_month_must_be_later(self):
        with self.assertRaises(ValueError):
            self.build(previous="2018-08", current="2018-07")

    def test_missing_product_reference_is_rejected(self):
        invalid_items = self.items.copy()
        invalid_items.loc[0, "product_id"] = "missing"

        with self.assertRaises(ValueError):
            build_product_revenue_diagnosis(
                "2018-07",
                "2018-08",
                self.orders,
                invalid_items,
                self.products,
                self.translations,
            )


if __name__ == "__main__":
    unittest.main()
