"""Revenue change decomposition using delivered orders and item value."""


def build_revenue_bridge(previous: dict, current: dict) -> dict:
    """Explain revenue change through order volume and average order value."""
    previous_orders = int(previous["delivered_order_count"])
    current_orders = int(current["delivered_order_count"])

    previous_revenue = float(previous["delivered_item_value"])
    current_revenue = float(current["delivered_item_value"])

    revenue_change = round(current_revenue - previous_revenue, 2)

    revenue_change_pct = (
        round((revenue_change / previous_revenue) * 100, 2)
        if previous_revenue != 0
        else None
    )

    previous_aov = (
        previous_revenue / previous_orders
        if previous_orders > 0
        else 0.0
    )
    current_aov = (
        current_revenue / current_orders
        if current_orders > 0
        else 0.0
    )

    volume_impact = (
        (current_orders - previous_orders)
        * (previous_aov + current_aov)
        / 2
    )

    average_order_value_impact = (
        (current_aov - previous_aov)
        * (previous_orders + current_orders)
        / 2
    )

    return {
        "previous_month": previous["month"],
        "current_month": current["month"],
        "previous_revenue": round(previous_revenue, 2),
        "current_revenue": round(current_revenue, 2),
        "revenue_change": revenue_change,
        "revenue_change_pct": revenue_change_pct,
        "previous_delivered_orders": previous_orders,
        "current_delivered_orders": current_orders,
        "previous_average_order_value": round(previous_aov, 2),
        "current_average_order_value": round(current_aov, 2),
        "volume_impact": round(volume_impact, 2),
        "average_order_value_impact": round(
            average_order_value_impact, 2
        ),
    }
