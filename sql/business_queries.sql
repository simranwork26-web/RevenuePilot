-- RevenuePilot: Business Analytics Queries
-- Run with: psql -d revenuepilot -f sql/business_queries.sql

-- 1. Monthly performance
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

-- 2. Top 10 product categories by delivered item value
SELECT
    category,
    delivered_item_count,
    delivered_order_count,
    delivered_item_value
FROM category_analytics
ORDER BY delivered_item_value DESC
LIMIT 10;

-- 3. Top 10 states by delivered item value
SELECT
    customer_state,
    delivered_order_count,
    unique_customer_count,
    delivered_item_value,
    average_delivered_item_value_per_order
FROM regional_analytics
ORDER BY delivered_item_value DESC
LIMIT 10;

-- 4. Customer segment distribution
SELECT
    segment,
    COUNT(*) AS customer_count,
    SUM(delivered_item_value) AS delivered_item_value,
    ROUND(AVG(recency_days), 1) AS average_recency_days
FROM customer_segmentation
GROUP BY segment
ORDER BY customer_count DESC;

-- 5. Repeat-customer summary
-- Count repeat customers only when they have at least one delivered order.
SELECT
    COUNT(*) FILTER (
        WHERE order_count >= 2 AND delivered_order_count > 0
    ) AS repeat_customers,
    COUNT(*) AS all_customers,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_count >= 2 AND delivered_order_count > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS repeat_customer_percentage,
    SUM(delivered_item_value)
        FILTER (
            WHERE order_count >= 2 AND delivered_order_count > 0
        ) AS repeat_customer_delivered_item_value
FROM customer_segmentation;

-- 6. Data-quality checks
SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT order_id) AS distinct_order_ids,
    COUNT(*) FILTER (WHERE customer_unique_id IS NULL)
        AS missing_customer_ids,
    COUNT(*) FILTER (WHERE order_purchase_timestamp IS NULL)
        AS missing_purchase_timestamps
FROM orders;
