
import unittest

import pandas as pd

from src.revenue_driver_drilldown import build_revenue_driver_drilldown


class TestRevenueDriverDrilldown(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "o1",
                "customer_id": "c1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-07-10 10:00:00",
            },
            {
                "order_id": "o2",
                "customer_id": "c2",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-08-10 10:00:00",
            },
            {
                "order_id": "o3",
                "customer_id": "c1",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-08-15 10:00:00",
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
                "price": 70.0,
            },
            {
                "order_id": "o3",
                "order_item_id": 1,
                "product_id": "p2",
                "price": 50.0,
            },
        ])

        self.products = pd.DataFrame([
            {"product_id": "p1", "product_category_name": "beauty"},
            {"product_id": "p2", "product_category_name": "tools"},
        ])

        self.customers = pd.DataFrame([
            {
                "customer_id": "c1",
                "customer_state": "SP",
            },
            {
                "customer_id": "c2",
                "customer_state": "RJ",
            },
        ])

        self.translations = pd.DataFrame([
            {
                "product_category_name": "beauty",
                "product_category_name_english": "health_beauty",
            },
        ])

    def build(self, **overrides):
        inputs = {
            "previous_month": "2018-07",
            "current_month": "2018-08",
            "orders": self.orders,
            "items": self.items,
            "products": self.products,
            "customers": self.customers,
            "translations": self.translations,
        }
        inputs.update(overrides)
        return build_revenue_driver_drilldown(**inputs)

    def test_calculates_monthly_revenue_change(self):
        result = self.build()

        self.assertEqual(result["previous_revenue"], 100.0)
        self.assertEqual(result["current_revenue"], 70.0)
        self.assertEqual(result["revenue_change"], -30.0)

    def test_excludes_non_delivered_revenue(self):
        result = self.build()

        self.assertEqual(result["current_revenue"], 70.0)

        tools = next(
            row
            for row in result["category_drivers"]
            if row["category"] == "tools"
        )
        self.assertEqual(tools["current_revenue"], 0.0)
        self.assertEqual(tools["revenue_change"], 0.0)

    def test_category_and_region_changes_reconcile(self):
        result = self.build()

        expected = result["revenue_change"]
        self.assertAlmostEqual(
            sum(row["revenue_change"] for row in result["category_drivers"]),
            expected,
        )
        self.assertAlmostEqual(
            sum(row["revenue_change"] for row in result["regional_drivers"]),
            expected,
        )

    def test_uses_translated_category_name(self):
        result = self.build()

        self.assertIn(
            "health_beauty",
            [row["category"] for row in result["category_drivers"]],
        )

    def test_rejects_invalid_month_format(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM"):
            self.build(previous_month="2018-7")

    def test_rejects_non_increasing_months(self):
        with self.assertRaisesRegex(ValueError, "later"):
            self.build(
                previous_month="2018-08",
                current_month="2018-08",
            )

    def test_rejects_months_without_source_orders(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.build(current_month="2018-09")

    def test_rejects_duplicate_order_ids(self):
        duplicate_orders = pd.concat(
            [self.orders, self.orders.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "unique"):
            self.build(orders=duplicate_orders)

    def test_rejects_duplicate_order_item_ids(self):
        duplicate_items = pd.concat(
            [self.items, self.items.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "unique"):
            self.build(items=duplicate_items)


if __name__ == "__main__":
    unittest.main()
