import unittest

import pandas as pd

from src.regional_analytics import build_regional_analytics


class TestRegionalAnalytics(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "o1",
                "customer_id": "c1",
                "order_status": "delivered",
            },
            {
                "order_id": "o2",
                "customer_id": "c2",
                "order_status": "canceled",
            },
            {
                "order_id": "o3",
                "customer_id": "c3",
                "order_status": "delivered",
            },
        ])

        self.customers = pd.DataFrame([
            {
                "customer_id": "c1",
                "customer_unique_id": "u1",
                "customer_state": "SP",
            },
            {
                "customer_id": "c2",
                "customer_unique_id": "u2",
                "customer_state": "SP",
            },
            {
                "customer_id": "c3",
                "customer_unique_id": "u3",
                "customer_state": "RJ",
            },
        ])

        self.items = pd.DataFrame([
            {
                "order_id": "o1",
                "order_item_id": 1,
                "price": 100.0,
                "freight_value": 10.0,
            },
            {
                "order_id": "o1",
                "order_item_id": 2,
                "price": 50.0,
                "freight_value": 5.0,
            },
            {
                "order_id": "o2",
                "order_item_id": 1,
                "price": 20.0,
                "freight_value": 2.0,
            },
        ])

    def test_aggregates_metrics_without_join_fanout(self):
        result = build_regional_analytics(
            self.orders, self.customers, self.items
        )
        sp = result.set_index("customer_state").loc["SP"]

        self.assertEqual(sp["order_count"], 2)
        self.assertEqual(sp["delivered_order_count"], 1)
        self.assertEqual(sp["unique_customer_count"], 2)
        self.assertAlmostEqual(sp["item_value_total"], 170.0)
        self.assertAlmostEqual(sp["delivered_item_value"], 150.0)
        self.assertAlmostEqual(sp["freight_value_total"], 17.0)
        self.assertAlmostEqual(
            sp["average_delivered_item_value_per_order"], 150.0
        )

    def test_preserves_orders_without_item_records(self):
        result = build_regional_analytics(
            self.orders, self.customers, self.items
        )
        rj = result.set_index("customer_state").loc["RJ"]

        self.assertEqual(rj["order_count"], 1)
        self.assertEqual(rj["delivered_order_count"], 1)
        self.assertAlmostEqual(rj["item_value_total"], 0.0)
        self.assertAlmostEqual(rj["delivered_item_value"], 0.0)
        self.assertAlmostEqual(
            rj["average_delivered_item_value_per_order"], 0.0
        )

    def test_regional_totals_reconcile_with_source(self):
        result = build_regional_analytics(
            self.orders, self.customers, self.items
        )

        self.assertEqual(result["order_count"].sum(), len(self.orders))
        self.assertAlmostEqual(
            result["item_value_total"].sum(), self.items["price"].sum()
        )
        self.assertAlmostEqual(
            result["freight_value_total"].sum(),
            self.items["freight_value"].sum(),
        )

    def test_rejects_duplicate_order_ids(self):
        duplicated = pd.concat(
            [self.orders, self.orders.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "Order IDs"):
            build_regional_analytics(
                duplicated, self.customers, self.items
            )

    def test_rejects_order_items_without_matching_order(self):
        orphan = self.items.copy()
        orphan.loc[0, "order_id"] = "missing_order"

        with self.assertRaisesRegex(ValueError, "do not match an order"):
            build_regional_analytics(
                self.orders, self.customers, orphan
            )

    def test_rejects_missing_required_columns(self):
        incomplete = self.customers.drop(columns=["customer_state"])

        with self.assertRaisesRegex(ValueError, "customer_state"):
            build_regional_analytics(
                self.orders, incomplete, self.items
            )


if __name__ == "__main__":
    unittest.main()
