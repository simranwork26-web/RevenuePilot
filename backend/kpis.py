from fastapi import APIRouter, HTTPException

from backend.database import get_connection

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/kpis")
def get_kpis() -> dict:
    """Return core RevenuePilot dashboard KPIs from PostgreSQL."""
    query = """
        SELECT
            COUNT(*) AS total_orders,
            COUNT(*) FILTER (
                WHERE order_status = 'delivered'
            ) AS delivered_orders,
            COUNT(DISTINCT customer_unique_id) AS unique_customers,
            COALESCE(
                SUM(item_value) FILTER (
                    WHERE order_status = 'delivered'
                ),
                0
            ) AS delivered_item_value
        FROM orders;
    """

    repeat_query = """
        SELECT
            COUNT(*) FILTER (
                WHERE order_count >= 2
            ) AS repeat_customers,
            COUNT(*) AS segmented_customers,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE order_count >= 2
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS repeat_customer_rate
        FROM customer_segmentation;
    """

    try:
        with get_connection() as conn:
            order_metrics = conn.execute(query).fetchone()
            customer_metrics = conn.execute(repeat_query).fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve dashboard KPIs from PostgreSQL.",
        ) from exc

    return {
        "total_orders": order_metrics["total_orders"],
        "delivered_orders": order_metrics["delivered_orders"],
        "unique_customers": order_metrics["unique_customers"],
        "delivered_item_value": float(
            order_metrics["delivered_item_value"]
        ),
        "repeat_customers": customer_metrics["repeat_customers"],
        "segmented_customers": customer_metrics["segmented_customers"],
        "repeat_customer_rate": float(
            customer_metrics["repeat_customer_rate"] or 0
        ),
    }
