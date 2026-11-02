
"""Evidence-based business recommendations from revenue driver data."""

from typing import Any


def build_business_recommendations(
    driver_data: dict[str, Any],
) -> dict[str, Any]:
    """Generate actionable recommendations from monthly revenue drivers."""
    recommendations: list[dict[str, Any]] = []

    previous_month = driver_data["previous_month"]
    current_month = driver_data["current_month"]
    overall_change = float(driver_data["revenue_change"])

    if overall_change < 0:
        recommendations.append(
            {
                "id": "overall_revenue_decline",
                "priority": "high",
                "title": "Investigate the overall revenue decline",
                "evidence": (
                    f"Revenue changed by {overall_change:.2f} "
                    f"from {previous_month} to {current_month}."
                ),
                "suggested_action": (
                    "Review the largest category and regional declines, "
                    "then check order volume, pricing, and product availability "
                    "before deciding on an intervention."
                ),
                "success_metric": "Month-over-month delivered revenue change",
                "metric_unit": "currency",
            }
        )

    for dimension, label in (
        ("category_drivers", "category"),
        ("regional_drivers", "customer state"),
    ):
        drivers = driver_data.get(dimension, [])

        declines = sorted(
            (
                row
                for row in drivers
                if float(row["revenue_change"]) < 0
            ),
            key=lambda row: float(row["revenue_change"]),
        )

        if declines:
            worst = declines[0]
            segment_name = (
                worst["category"]
                if label == "category"
                else worst["customer_state"]
            )
            change = float(worst["revenue_change"])

            recommendations.append(
                {
                    "id": f"{label.replace(' ', '_')}_revenue_decline",
                    "priority": "high" if change <= -10000 else "medium",
                    "title": f"Investigate the largest {label} revenue decline",
                    "segment": segment_name,
                    "evidence": (
                        f"{segment_name} revenue changed by {change:.2f}, "
                        f"from {float(worst['previous_revenue']):.2f} "
                        f"to {float(worst['current_revenue']):.2f}."
                    ),
                    "revenue_change": round(change, 2),
                    "suggested_action": (
                        f"Compare order counts and average order value for "
                        f"{segment_name} across both months. Check product "
                        "availability, delivery issues, and changes in the "
                        "customer or product mix before taking action."
                    ),
                    "success_metric": "Segment month-over-month revenue change",
                    "metric_unit": "currency",
                }
            )

    recommendations.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["priority"]],
            float(item.get("revenue_change", overall_change)),
        )
    )

    return {
        "previous_month": previous_month,
        "current_month": current_month,
        "overall_revenue_change": round(overall_change, 2),
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "limitations": [
            "Revenue changes identify where to investigate; they do not establish why revenue changed.",
            "Recommendations are based on the two selected months and do not establish a long-term trend.",
        ],
    }
