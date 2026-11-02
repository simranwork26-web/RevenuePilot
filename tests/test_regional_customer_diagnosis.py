import unittest

import pandas as pd

from src.regional_customer_diagnosis import (
    build_regional_customer_diagnosis,
)


class TestRegionalCustomerDiagnosis(unittest.TestCase):

    def setUp(self):
        self.orders = pd.DataFrame([
            {
                "order_id": "o1",
                "customer_id": "c1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-07-05",
            },
            {
                "order_id": "o2",
                "customer_id": "c2",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-07-10",
            },
            {
                "order_id": "o3",
                "customer_id": "c1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-08-05",
            },
            {
                "order_id": "o4",
                "customer_id": "c3",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-08-12",
            },
            {
                "order_id": "o5",
                "customer_id": "c4",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-08-15",
            },
        ])

        self.items = pd.DataFrame([
            {"order_id": "o1", "price": 100.0},
            {"order_id": "o2", "price": 200.0},
            {"order_id": "o3", "price": 80.0},
            {"order_id": "o4", "price": 120.0},
            {"order_id": "o5", "price": 500.0},
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
                "customer_state": "RJ",
            },
            {
                "customer_id": "c3",
                "customer_unique_id": "u3",
                "customer_state": "SP",
            },
            {
                "customer_id": "c4",
                "customer_unique_id": "u4",
                "customer_state": "MG",
            },
        ])

    def build(self, **overrides):
        arguments = {
            "previous_month": "2018-07",
            "current_month": "2018-08",
            "orders": self.orders,
            "items": self.items,
            "customers": self.customers,
        }
        arguments.update(overrides)
        return build_regional_customer_diagnosis(**arguments)

    def test_overall_revenue_change(self):
        result = self.build()

        self.assertEqual(result["previous_revenue"], 300.0)
        self.assertEqual(result["current_revenue"], 200.0)
        self.assertEqual(result["revenue_change"], -100.0)

    def test_regional_revenue_reconciles(self):
        result = self.build()

        regional_change = sum(
            row["revenue_change"]
            for row in result["regional_drivers"]
        )

        self.assertAlmostEqual(regional_change, -100.0)

    def test_customer_revenue_reconciles(self):
        result = self.build()

        customer_change = sum(
            row["revenue_change"]
            for row in result["customer_segments"]
        )

        self.assertAlmostEqual(customer_change, -100.0)

    def test_new_retained_and_inactive_customers(self):
        result = self.build()
        segments = {
            row["status"]: row
            for row in result["customer_segments"]
        }

        self.assertEqual(segments["new"]["customers"], 1)
        self.assertEqual(segments["retained"]["customers"], 1)
        self.assertEqual(segments["inactive"]["customers"], 1)

        self.assertEqual(segments["new"]["current_revenue"], 120.0)
        self.assertEqual(segments["retained"]["revenue_change"], -20.0)
        self.assertEqual(segments["inactive"]["previous_revenue"], 200.0)

    def test_cancelled_orders_are_excluded(self):
        result = self.build()

        self.assertEqual(result["current_revenue"], 200.0)
        self.assertNotIn(
            "MG",
            [row["state"] for row in result["regional_drivers"]],
        )

    def test_multiple_orders_from_same_customer(self):
        extra_order = pd.DataFrame([{
            "order_id": "o6",
            "customer_id": "c1",
            "order_status": "delivered",
            "order_purchase_timestamp": "2018-08-20",
        }])

        extra_item = pd.DataFrame([{
            "order_id": "o6",
            "price": 40.0,
        }])

        result = self.build(
            orders=pd.concat(
                [self.orders, extra_order],
                ignore_index=True,
            ),
            items=pd.concat(
                [self.items, extra_item],
                ignore_index=True,
            ),
        )

        retained = next(
            row for row in result["customer_segments"]
            if row["status"] == "retained"
        )

        self.assertEqual(retained["customers"], 1)
        self.assertEqual(retained["current_delivered_orders"], 2)
        self.assertEqual(retained["current_revenue"], 120.0)

    def test_invalid_month_format_is_rejected(self):
        with self.assertRaises(ValueError):
            self.build(previous_month="July 2018")

    def test_reversed_months_are_rejected(self):
        with self.assertRaises(ValueError):
            self.build(
                previous_month="2018-08",
                current_month="2018-07",
            )

    def test_duplicate_order_ids_are_rejected(self):
        duplicate_orders = pd.concat(
            [self.orders, self.orders.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaises(ValueError):
            self.build(orders=duplicate_orders)

    def test_duplicate_customer_ids_are_rejected(self):
        duplicate_customers = pd.concat(
            [self.customers, self.customers.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaises(ValueError):
            self.build(customers=duplicate_customers)

    def test_missing_customer_reference_is_rejected(self):
        incomplete_customers = self.customers[
            self.customers["customer_id"] != "c1"
        ]

        with self.assertRaises(ValueError):
            self.build(customers=incomplete_customers)

    def test_missing_required_column_is_rejected(self):
        incomplete_items = self.items.drop(columns=["price"])

        with self.assertRaises(ValueError):
            self.build(items=incomplete_items)


if __name__ == "__main__":
    unittest.main()
