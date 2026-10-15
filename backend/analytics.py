from fastapi import APIRouter, HTTPException

from backend.database import get_connection

from src.evaluate_revenue_forecast import load_weekly_revenue
from src.revenue_forecasting import (
    evaluate_linear_trend,
    forecast_linear_trend,
)

router = APIRouter(prefix="/api", tags=["Analytics"])


def fetch_all(query: str) -> list[dict]:
    """Execute a read-only analytics query and return JSON-ready rows."""
    try:
        with get_connection() as conn:
            rows = conn.execute(query).fetchall()
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
    evaluation = evaluate_linear_trend(weekly_data, test_weeks=12)
    forecast = forecast_linear_trend(weekly_data, horizon=4)

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
