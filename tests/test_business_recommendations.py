
from backend.business_recommendations import build_business_recommendations


def test_overall_revenue_decline_creates_high_priority_recommendation():
    driver_data = {
        "previous_month": "2018-07",
        "current_month": "2018-08",
        "previous_revenue": 100000.0,
        "current_revenue": 85000.0,
        "revenue_change": -15000.0,
        "category_drivers": [],
        "regional_drivers": [],
    }

    result = build_business_recommendations(driver_data)

    assert result["overall_revenue_change"] == -15000.0
    assert result["recommendation_count"] == 1

    recommendation = result["recommendations"][0]

    assert recommendation["id"] == "overall_revenue_decline"
    assert recommendation["priority"] == "high"
    assert "Investigate" in recommendation["title"]
    assert recommendation["success_metric"] == (
        "Month-over-month delivered revenue change"
    )

def test_largest_category_decline_creates_segment_recommendation():
    driver_data = {
        "previous_month": "2018-07",
        "current_month": "2018-08",
        "previous_revenue": 100000.0,
        "current_revenue": 110000.0,
        "revenue_change": 10000.0,
        "category_drivers": [
            {
                "category": "watches_gifts",
                "previous_revenue": 30000.0,
                "current_revenue": 15000.0,
                "revenue_change": -15000.0,
            },
            {
                "category": "health_beauty",
                "previous_revenue": 20000.0,
                "current_revenue": 18000.0,
                "revenue_change": -2000.0,
            },
        ],
        "regional_drivers": [],
    }

    result = build_business_recommendations(driver_data)

    category_recommendations = [
        item
        for item in result["recommendations"]
        if item["id"] == "category_revenue_decline"
    ]

    assert len(category_recommendations) == 1
    assert category_recommendations[0]["segment"] == "watches_gifts"
    assert category_recommendations[0]["priority"] == "high"
    assert category_recommendations[0]["revenue_change"] == -15000.0


def test_largest_regional_decline_creates_segment_recommendation():
    driver_data = {
        "previous_month": "2018-07",
        "current_month": "2018-08",
        "previous_revenue": 100000.0,
        "current_revenue": 100000.0,
        "revenue_change": 0.0,
        "category_drivers": [],
        "regional_drivers": [
            {
                "customer_state": "SP",
                "previous_revenue": 50000.0,
                "current_revenue": 40000.0,
                "revenue_change": -10000.0,
            },
            {
                "customer_state": "RJ",
                "previous_revenue": 20000.0,
                "current_revenue": 18000.0,
                "revenue_change": -2000.0,
            },
        ],
    }

    result = build_business_recommendations(driver_data)

    regional_recommendations = [
        item
        for item in result["recommendations"]
        if item["id"] == "customer_state_revenue_decline"
    ]

    assert len(regional_recommendations) == 1
    assert regional_recommendations[0]["segment"] == "SP"
    assert regional_recommendations[0]["priority"] == "high"
    assert regional_recommendations[0]["revenue_change"] == -10000.0

def test_revenue_growth_does_not_create_decline_recommendation():
    driver_data = {
        "previous_month": "2018-07",
        "current_month": "2018-08",
        "previous_revenue": 100000.0,
        "current_revenue": 125000.0,
        "revenue_change": 25000.0,
        "category_drivers": [
            {
                "category": "health_beauty",
                "previous_revenue": 20000.0,
                "current_revenue": 25000.0,
                "revenue_change": 5000.0,
            }
        ],
        "regional_drivers": [
            {
                "customer_state": "SP",
                "previous_revenue": 30000.0,
                "current_revenue": 35000.0,
                "revenue_change": 5000.0,
            }
        ],
    }

    result = build_business_recommendations(driver_data)

    assert result["overall_revenue_change"] == 25000.0
    assert result["recommendation_count"] == 0
    assert result["recommendations"] == []


def test_no_revenue_change_creates_no_recommendations():
    driver_data = {
        "previous_month": "2018-07",
        "current_month": "2018-08",
        "previous_revenue": 100000.0,
        "current_revenue": 100000.0,
        "revenue_change": 0.0,
        "category_drivers": [],
        "regional_drivers": [],
    }

    result = build_business_recommendations(driver_data)

    assert result["recommendation_count"] == 0
    assert result["recommendations"] == []
    assert len(result["limitations"]) == 2
