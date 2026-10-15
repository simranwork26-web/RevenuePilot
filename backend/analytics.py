from fastapi import APIRouter, HTTPException

from backend.database import get_connection

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
