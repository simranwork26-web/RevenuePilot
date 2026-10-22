from fastapi import APIRouter, HTTPException

from backend.database import get_connection
from backend.customer_cohorts import (
    COHORT_QUERY,
    build_cohort_retention,
)
from backend.retention_insights import build_retention_insights
from datetime import date
from fastapi import Query
from backend.revenue_bridge import build_revenue_bridge
from src.revenue_driver_drilldown import load_revenue_driver_drilldown

from src.evaluate_revenue_forecast import load_weekly_revenue
from src.revenue_forecasting import (
    evaluate_damped_trend,
    forecast_damped_trend,
)

router = APIRouter(prefix="/api", tags=["Analytics"])


def fetch_all(query: str, params: tuple | None = None) -> list[dict]:
    """Execute a read-only analytics query and return JSON-ready rows."""
    try:
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall() if params is not None else conn.execute(query).fetchall()
            return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve analytics from PostgreSQL.",
        ) from exc


@router.get("/revenue/monthly")
def get_monthly_revenue() -> list[dict]:
    rows = fetch_all("""
        SELECT
            month,
            order_count,
            delivered_order_count,
            item_value_total,
            delivered_item_value,
            recorded_payment_value_total,
            low_volume_month
        FROM monthly_revenue_analytics
        ORDER BY month;
    """)
    return [
        {
            **row,
            "month": row["month"].isoformat(),
            "item_value_total": float(row["item_value_total"]),
            "delivered_item_value": float(row["delivered_item_value"]),
            "recorded_payment_value_total": float(
                row["recorded_payment_value_total"]
            ),
        }
        for row in rows
    ]


@router.get("/revenue/bridge")
def get_revenue_bridge(
    previous_month: str = Query(..., description="Previous month in YYYY-MM format"),
    current_month: str = Query(..., description="Current month in YYYY-MM format"),
) -> dict:
    """Explain delivered item revenue change between two months."""
    try:
        previous_date = date.fromisoformat(f"{previous_month}-01")
        current_date = date.fromisoformat(f"{current_month}-01")
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Months must use YYYY-MM format.",
        ) from exc

    if previous_date.strftime("%Y-%m") != previous_month or current_date.strftime("%Y-%m") != current_month:
        raise HTTPException(
            status_code=400,
            detail="Months must use YYYY-MM format.",
        )

    if current_date <= previous_date:
        raise HTTPException(
            status_code=400,
            detail="current_month must be later than previous_month.",
        )

    rows = fetch_all(
        """
        SELECT
            month,
            delivered_order_count,
            delivered_item_value
        FROM monthly_revenue_analytics
        WHERE month IN (%s, %s)
        ORDER BY month;
        """,
        (previous_date, current_date),
    )

    by_month = {
        row["month"].isoformat(): {
            **row,
            "month": row["month"].isoformat(),
            "delivered_order_count": int(row["delivered_order_count"]),
            "delivered_item_value": float(row["delivered_item_value"]),
        }
        for row in rows
    }

    previous_key = previous_date.isoformat()
    current_key = current_date.isoformat()

    if previous_key not in by_month or current_key not in by_month:
        raise HTTPException(
            status_code=404,
            detail="One or both selected months are unavailable.",
        )

    return build_revenue_bridge(
        by_month[previous_key],
        by_month[current_key],
    )


@router.get("/revenue/drivers")
def get_revenue_driver_drilldown(
    previous_month: str = Query(...),
    current_month: str = Query(...),
) -> dict:
    """Break down delivered revenue changes by category and customer state."""
    try:
        return load_revenue_driver_drilldown(previous_month, current_month)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "months are unavailable" in message.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc


@router.get("/categories")
def get_categories() -> list[dict]:
    rows = fetch_all("""
        SELECT
            category,
            item_count,
            order_count,
            delivered_item_count,
            delivered_order_count,
            item_value_total,
            delivered_item_value
        FROM category_analytics
        ORDER BY delivered_item_value DESC
        LIMIT 10;
    """)
    return [
        {
            **row,
            "item_value_total": float(row["item_value_total"]),
            "delivered_item_value": float(row["delivered_item_value"]),
        }
        for row in rows
    ]


@router.get("/regions")
def get_regions() -> list[dict]:
    rows = fetch_all("""
        SELECT
            customer_state,
            order_count,
            delivered_order_count,
            unique_customer_count,
            item_value_total,
            delivered_item_value,
            freight_value_total,
            average_delivered_item_value_per_order
        FROM regional_analytics
        ORDER BY delivered_item_value DESC
        LIMIT 10;
    """)
    return [
        {
            **row,
            "item_value_total": float(row["item_value_total"]),
            "delivered_item_value": float(row["delivered_item_value"]),
            "freight_value_total": float(row["freight_value_total"]),
            "average_delivered_item_value_per_order": (
                float(row["average_delivered_item_value_per_order"])
                if row["average_delivered_item_value_per_order"] is not None
                else None
            ),
        }
        for row in rows
    ]


@router.get("/customers/segments")
def get_customer_segments() -> list[dict]:
    rows = fetch_all("""
        SELECT
            segment,
            COUNT(*) AS customer_count,
            COALESCE(SUM(delivered_item_value), 0)
                AS delivered_item_value,
            ROUND(AVG(recency_days), 1) AS average_recency_days
        FROM customer_segmentation
        GROUP BY segment
        ORDER BY customer_count DESC;
    """)
    return [
        {
            **row,
            "delivered_item_value": float(row["delivered_item_value"]),
            "average_recency_days": (
                float(row["average_recency_days"])
                if row["average_recency_days"] is not None
                else None
            ),
        }
        for row in rows
    ]

@router.get("/customers/cohorts")
def get_customer_cohorts() -> dict:
    """Return monthly delivered-order customer cohort retention."""
    rows = fetch_all(COHORT_QUERY)
    return build_cohort_retention(rows)


@router.get("/customers/retention-insights")
def get_customer_retention_insights() -> dict:
    """Return descriptive insights from monthly customer cohorts."""
    rows = fetch_all(COHORT_QUERY)
    cohort_data = build_cohort_retention(rows)
    return build_retention_insights(cohort_data["cohorts"])


@router.get("/customers/retention")
def get_customer_retention() -> dict:
    """Return the observed 90-day second-order rate for eligible customers."""
    rows = fetch_all("""
        WITH customer_order_ranks AS (
            SELECT
                customer_unique_id,
                order_purchase_timestamp,
                ROW_NUMBER() OVER (
                    PARTITION BY customer_unique_id
                    ORDER BY order_purchase_timestamp, order_id
                ) AS order_rank
            FROM orders
            WHERE customer_unique_id IS NOT NULL
              AND order_purchase_timestamp IS NOT NULL
        ),
        customer_first_second AS (
            SELECT
                customer_unique_id,
                MIN(order_purchase_timestamp) FILTER (
                    WHERE order_rank = 1
                ) AS first_order,
                MIN(order_purchase_timestamp) FILTER (
                    WHERE order_rank = 2
                ) AS second_order
            FROM customer_order_ranks
            GROUP BY customer_unique_id
        )
        SELECT
            COUNT(*) FILTER (
                WHERE DATE '2018-10-18' - first_order::date >= 90
            ) AS eligible_customers,
            COUNT(*) FILTER (
                WHERE second_order IS NOT NULL
                  AND DATE '2018-10-18' - first_order::date >= 90
                  AND second_order <= first_order + INTERVAL '90 days'
            ) AS customers_with_second_order_within_90_days,
            ROUND(
                (
                    100.0 * COUNT(*) FILTER (
                        WHERE second_order IS NOT NULL
                          AND DATE '2018-10-18' - first_order::date >= 90
                          AND second_order <= first_order + INTERVAL '90 days'
                    )
                    / NULLIF(
                        COUNT(*) FILTER (
                            WHERE DATE '2018-10-18' - first_order::date >= 90
                        ),
                        0
                    )
                )::numeric,
                2
            ) AS second_order_within_90_days_pct
        FROM customer_first_second;
    """)
    return rows[0]

@router.get("/revenue/forecast")
def get_revenue_forecast() -> dict:
    """Return a four-week historical-data revenue forecast."""
    weekly_data = load_weekly_revenue()
    evaluation = evaluate_damped_trend(
        weekly_data, test_weeks=12, damping_factor=0.25
    )
    forecast = forecast_damped_trend(
        weekly_data, horizon=4, damping_factor=0.25
    )

    return {
        "forecast_horizon_weeks": 4,
        "revenue_metric": "delivered_item_revenue",
        "currency": "BRL",
        "historical_cutoff": (
            weekly_data["week_start"].max().isoformat()
        ),
        "forecast_status": "historical_demo",
        "evaluation": evaluation,
        "forecast": [
            {
                "week_start": row["week_start"].isoformat(),
                "forecast_revenue": round(
                    float(row["forecast_revenue"]), 2
                ),
            }
            for _, row in forecast.iterrows()
        ],
    }
