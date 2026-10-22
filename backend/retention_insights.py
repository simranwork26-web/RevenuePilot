"""Evidence-based insights derived from monthly customer cohort retention."""

from statistics import mean

MIN_COHORT_SIZE = 100
MIN_COMPARABLE_COHORTS = 3


def build_retention_insights(cohorts: list[dict]) -> dict:
    """Compare sufficiently large cohorts at the same age."""
    valid_cohorts = [
        cohort
        for cohort in cohorts
        if int(cohort.get("cohort_size", 0)) > 0
    ]

    small_cohorts = [
        {
            "cohort_month": cohort["cohort_month"],
            "cohort_size": int(cohort["cohort_size"]),
        }
        for cohort in valid_cohorts
        if int(cohort["cohort_size"]) < MIN_COHORT_SIZE
    ]

    eligible_cohorts = [
        cohort
        for cohort in valid_cohorts
        if int(cohort["cohort_size"]) >= MIN_COHORT_SIZE
    ]

    comparable_month = None
    comparable = []

    observed_ages = sorted(
        {
            int(month)
            for cohort in eligible_cohorts
            for month in cohort.get("retention", {})
            if int(month) >= 1
        },
        reverse=True,
    )

    for age in observed_ages:
        eligible = [
            {
                "cohort_month": cohort["cohort_month"],
                "cohort_size": int(cohort["cohort_size"]),
                "retention_pct": float(cohort["retention"][str(age)]),
            }
            for cohort in eligible_cohorts
            if str(age) in cohort.get("retention", {})
        ]

        if len(eligible) >= MIN_COMPARABLE_COHORTS:
            comparable_month = age
            comparable = eligible
            break

    comparison = None

    if len(comparable) >= MIN_COMPARABLE_COHORTS:
        rates = [item["retention_pct"] for item in comparable]
        all_zero = all(rate == 0 for rate in rates)
        comparison = {
            "month_number": comparable_month,
            "cohort_count": len(comparable),
            "average_retention_pct": round(mean(rates), 2),
            "highest": max(comparable, key=lambda item: item["retention_pct"]),
            "lowest": min(comparable, key=lambda item: item["retention_pct"]),
            "status": (
                "no_observed_repeat_activity"
                if all_zero
                else "retention_observed"
            ),
            "interpretation": (
                "No repeat delivered orders were recorded in this specific calendar "
                "month for the eligible cohorts. This does not mean those "
                "customers never returned in another month."
                if all_zero
                else
                "Only cohorts with at least 100 customers are compared, "
                "at the same age. Differences are descriptive and do not "
                "establish causation."
            ),
        }

    return {
        "minimum_cohort_size": MIN_COHORT_SIZE,
        "small_cohort_count": len(small_cohorts),
        "small_cohorts": small_cohorts,
        "comparable_retention": comparison,
    }
