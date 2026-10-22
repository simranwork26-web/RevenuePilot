"""Monthly customer cohort retention analytics for historical Olist data."""

from datetime import date


REFERENCE_DATE = date(2018, 10, 18)


COHORT_QUERY = """
WITH delivered_orders AS (
    SELECT DISTINCT
        customer_unique_id,
        DATE_TRUNC('month', order_purchase_timestamp)::date AS order_month
    FROM orders
    WHERE order_status = 'delivered'
      AND customer_unique_id IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
),
customer_cohorts AS (
    SELECT
        customer_unique_id,
        MIN(order_month) AS cohort_month
    FROM delivered_orders
    GROUP BY customer_unique_id
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),
observation_cutoff AS (
    SELECT MAX(order_month) AS historical_cutoff
    FROM delivered_orders
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        d.order_month,
        (
            (EXTRACT(YEAR FROM d.order_month)
             - EXTRACT(YEAR FROM c.cohort_month)) * 12
            + EXTRACT(MONTH FROM d.order_month)
            - EXTRACT(MONTH FROM c.cohort_month)
        )::integer AS month_number,
        COUNT(DISTINCT d.customer_unique_id) AS active_customers
    FROM customer_cohorts c
    JOIN delivered_orders d
      ON d.customer_unique_id = c.customer_unique_id
    GROUP BY c.cohort_month, d.order_month
),
cohort_months AS (
    SELECT
        s.cohort_month,
        s.cohort_size,
        series.month_number,
        (s.cohort_month
         + (series.month_number || ' months')::interval)::date AS activity_month,
        o.historical_cutoff
    FROM cohort_sizes s
    CROSS JOIN observation_cutoff o
    CROSS JOIN LATERAL GENERATE_SERIES(
        0,
        (
            (EXTRACT(YEAR FROM o.historical_cutoff)
             - EXTRACT(YEAR FROM s.cohort_month)) * 12
            + EXTRACT(MONTH FROM o.historical_cutoff)
            - EXTRACT(MONTH FROM s.cohort_month)
        )::integer
    ) AS series(month_number)
)
SELECT
    m.cohort_month,
    m.cohort_size,
    m.month_number,
    m.historical_cutoff,
    COALESCE(a.active_customers, 0) AS active_customers,
    ROUND(
        100.0 * COALESCE(a.active_customers, 0)
        / NULLIF(m.cohort_size, 0),
        2
    ) AS retention_pct
FROM cohort_months m
LEFT JOIN cohort_activity a
  ON a.cohort_month = m.cohort_month
 AND a.month_number = m.month_number
ORDER BY m.cohort_month, m.month_number;
"""


def build_cohort_retention(rows: list[dict]) -> dict:
    """Convert cohort activity rows into a JSON-ready retention matrix."""
    if not rows:
        return {
            "reference_date": REFERENCE_DATE.isoformat(),
            "historical_cutoff": None,
            "cohort_count": 0,
            "cohorts": [],
        }

    cohorts: dict[date, dict] = {}
    historical_cutoff = max(row["historical_cutoff"] for row in rows)

    for row in rows:
        cohort_month = row["cohort_month"]
        month_number = int(row["month_number"])

        if cohort_month not in cohorts:
            cohorts[cohort_month] = {
                "cohort_month": cohort_month.isoformat(),
                "cohort_size": int(row["cohort_size"]),
                "retention": {},
            }

        cohorts[cohort_month]["retention"][str(month_number)] = (
            float(row["retention_pct"])
        )

    cohort_list = []
    for _, cohort in sorted(cohorts.items()):
        cohort["retention"] = dict(
            sorted(
                cohort["retention"].items(),
                key=lambda item: int(item[0]),
            )
        )
        cohort_list.append(cohort)

    return {
        "reference_date": REFERENCE_DATE.isoformat(),
        "historical_cutoff": historical_cutoff.isoformat(),
        "cohort_count": len(cohort_list),
        "cohorts": cohort_list,
    }
