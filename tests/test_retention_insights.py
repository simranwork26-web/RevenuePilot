"""Tests for evidence-based customer retention insights."""

import unittest

from backend.retention_insights import build_retention_insights


class TestRetentionInsights(unittest.TestCase):

    def test_empty_cohorts(self):
        result = build_retention_insights([])

        self.assertEqual(result["small_cohort_count"], 0)
        self.assertIsNone(result["comparable_retention"])

    def test_flags_small_cohorts(self):
        cohorts = [
            {
                "cohort_month": "2018-01-01",
                "cohort_size": 1,
                "retention": {"0": 100.0, "1": 0.0},
            },
            {
                "cohort_month": "2018-02-01",
                "cohort_size": 150,
                "retention": {"0": 100.0, "1": 5.0},
            },
        ]

        result = build_retention_insights(cohorts)

        self.assertEqual(result["small_cohort_count"], 1)
        self.assertEqual(
            result["small_cohorts"][0]["cohort_month"],
            "2018-01-01",
        )

    def test_compares_cohorts_at_same_age(self):
        cohorts = [
            {
                "cohort_month": "2018-01-01",
                "cohort_size": 200,
                "retention": {"0": 100.0, "1": 10.0, "2": 5.0},
            },
            {
                "cohort_month": "2018-02-01",
                "cohort_size": 300,
                "retention": {"0": 100.0, "1": 20.0, "2": 15.0},
            },
            {
                "cohort_month": "2018-03-01",
                "cohort_size": 400,
                "retention": {"0": 100.0, "1": 30.0},
            },
        ]

        result = build_retention_insights(cohorts)
        comparison = result["comparable_retention"]

        self.assertEqual(comparison["month_number"], 1)
        self.assertEqual(comparison["cohort_count"], 3)
        self.assertEqual(comparison["average_retention_pct"], 20.0)
        self.assertEqual(comparison["highest"]["retention_pct"], 30.0)
        self.assertEqual(comparison["lowest"]["retention_pct"], 10.0)

    def test_does_not_compare_fewer_than_three_cohorts(self):
        cohorts = [
            {
                "cohort_month": "2018-01-01",
                "cohort_size": 200,
                "retention": {"0": 100.0, "1": 10.0},
            },
            {
                "cohort_month": "2018-02-01",
                "cohort_size": 300,
                "retention": {"0": 100.0, "1": 20.0},
            },
        ]

        result = build_retention_insights(cohorts)

        self.assertIsNone(result["comparable_retention"])


if __name__ == "__main__":
    unittest.main()


class TestUnevenCohortMaturity(unittest.TestCase):

    def test_uses_latest_age_with_three_observed_cohorts(self):
        cohorts = [
            {
                "cohort_month": "2018-01-01",
                "cohort_size": 200,
                "retention": {"0": 100.0, "1": 10.0, "2": 5.0, "3": 2.0},
            },
            {
                "cohort_month": "2018-02-01",
                "cohort_size": 300,
                "retention": {"0": 100.0, "1": 20.0, "2": 15.0},
            },
            {
                "cohort_month": "2018-03-01",
                "cohort_size": 400,
                "retention": {"0": 100.0, "1": 30.0, "2": 25.0},
            },
            {
                "cohort_month": "2018-04-01",
                "cohort_size": 500,
                "retention": {"0": 100.0, "1": 40.0},
            },
        ]

        result = build_retention_insights(cohorts)
        comparison = result["comparable_retention"]

        self.assertEqual(comparison["month_number"], 2)
        self.assertEqual(comparison["cohort_count"], 3)
        self.assertEqual(comparison["average_retention_pct"], 15.0)


class TestZeroRetentionInterpretation(unittest.TestCase):

    def test_all_zero_rates_are_labelled_as_no_repeat_activity(self):
        cohorts = [
            {
                "cohort_month": "2017-01-01",
                "cohort_size": 200,
                "retention": {"0": 100.0, "1": 0.0},
            },
            {
                "cohort_month": "2017-02-01",
                "cohort_size": 300,
                "retention": {"0": 100.0, "1": 0.0},
            },
            {
                "cohort_month": "2017-03-01",
                "cohort_size": 400,
                "retention": {"0": 100.0, "1": 0.0},
            },
        ]

        result = build_retention_insights(cohorts)
        comparison = result["comparable_retention"]

        self.assertEqual(comparison["average_retention_pct"], 0.0)
        self.assertEqual(comparison["status"], "no_observed_repeat_activity")
