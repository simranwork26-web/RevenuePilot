"""Tests for monthly customer cohort retention formatting."""

import unittest
from datetime import date
from decimal import Decimal

from backend.customer_cohorts import build_cohort_retention


class TestCustomerCohorts(unittest.TestCase):

    def test_empty_rows(self):
        result = build_cohort_retention([])

        self.assertEqual(result["cohort_count"], 0)
        self.assertIsNone(result["historical_cutoff"])
        self.assertEqual(result["cohorts"], [])

    def test_retention_and_zero_activity(self):
        rows = [
            {
                "cohort_month": date(2018, 6, 1),
                "cohort_size": 100,
                "month_number": 0,
                "historical_cutoff": date(2018, 8, 1),
                "retention_pct": Decimal("100.00"),
            },
            {
                "cohort_month": date(2018, 6, 1),
                "cohort_size": 100,
                "month_number": 1,
                "historical_cutoff": date(2018, 8, 1),
                "retention_pct": Decimal("0.00"),
            },
            {
                "cohort_month": date(2018, 6, 1),
                "cohort_size": 100,
                "month_number": 2,
                "historical_cutoff": date(2018, 8, 1),
                "retention_pct": Decimal("4.50"),
            },
        ]

        result = build_cohort_retention(rows)

        self.assertEqual(result["cohort_count"], 1)
        self.assertEqual(result["historical_cutoff"], "2018-08-01")
        self.assertEqual(
            result["cohorts"][0]["retention"],
            {"0": 100.0, "1": 0.0, "2": 4.5},
        )

    def test_unobserved_months_are_omitted(self):
        rows = [
            {
                "cohort_month": date(2018, 8, 1),
                "cohort_size": 6144,
                "month_number": 0,
                "historical_cutoff": date(2018, 8, 1),
                "retention_pct": Decimal("100.00"),
            }
        ]

        result = build_cohort_retention(rows)

        self.assertEqual(
            result["cohorts"][0]["retention"],
            {"0": 100.0},
        )
        self.assertNotIn("1", result["cohorts"][0]["retention"])

    def test_cohorts_are_sorted(self):
        rows = [
            {
                "cohort_month": date(2018, 8, 1),
                "cohort_size": 20,
                "month_number": 0,
                "historical_cutoff": date(2018, 8, 1),
                "retention_pct": Decimal("100.00"),
            },
            {
                "cohort_month": date(2018, 7, 1),
                "cohort_size": 10,
                "month_number": 0,
                "historical_cutoff": date(2018, 8, 1),
                "retention_pct": Decimal("100.00"),
            },
        ]

        result = build_cohort_retention(rows)

        self.assertEqual(
            [c["cohort_month"] for c in result["cohorts"]],
            ["2018-07-01", "2018-08-01"],
        )


if __name__ == "__main__":
    unittest.main()
