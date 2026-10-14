# Customer Segmentation and Retention Insights

## Objective
Analyze customer purchasing frequency, delivered-order activity, delivered item value, and purchase recency.

## Input and Output
- Input: data/processed/orders_analytics.csv
- Source: src/customer_segmentation.py
- Output: data/processed/customer_segmentation.csv
- Fixed reference date: 2018-10-18

## Customer Metrics
- order_count: Number of recorded orders per unique customer.
- first_purchase: Earliest purchase timestamp.
- last_purchase: Latest purchase timestamp.
- delivered_order_count: Number of delivered orders.
- delivered_item_value: Item value from delivered orders only.
- delivered_payment_value: Recorded payment value from delivered orders only.
- recency_days: Calendar days between the reference date and last purchase.
- segment: Assigned customer segment.

Customers are grouped by customer_unique_id. Item value and payment value remain separate. Item value is not profit or audited accounting revenue.

## Segment Definitions
Segments are mutually exclusive, using this priority:

1. No delivered order: No delivered orders, regardless of recorded order count.
2. One-time: Exactly one recorded order and at least one delivered order.
3. High-value repeat: At least two recorded orders, at least one delivered order, and delivered item value at or above the threshold.
4. Repeat: Customers who do not match the preceding categories.

The high-value threshold is the 90th percentile of delivered item value among customers with at least two recorded orders and at least one delivered order.

## Current Results
- Unique customers: 96,096
- No delivered order: 2,738
- One-time: 90,379
- Repeat: 2,681
- High-value repeat: 298
- High-value repeat threshold: 499.15
- Total delivered item value: 13,221,498.11

These results are descriptive. They do not establish customer lifetime value, profitability, or causation.

## Validation and Limitations
The module validates required columns, unique order IDs, customer identifiers, purchase timestamps, and the reference date. It preserves all unique customers and keeps delivered item value separate from payment value.

The fixed reference date is the day after the latest recorded purchase in the current dataset. The threshold may change if the dataset changes. Multiple recorded orders without a delivered order are classified as No delivered order. Historical data alone does not explain why customers did not return.

## Reproduction
Run the module from the project root using .venv/bin/python -m src.customer_segmentation.

Run the customer tests using .venv/bin/python -m unittest discover -s tests -p 'test_customer_segmentation.py' -v.
