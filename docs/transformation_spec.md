# RevenuePilot — Transformation Specification

## 1. Objective

Create reproducible processed datasets for revenue analysis, customer
intelligence, SQL analytics, Power BI dashboards, and forecasting.

## 2. First output: Order-level analytical dataset

Planned output:
- `data/processed/orders_analytics.csv`

Grain:
- Exactly one row per `order_id`.

## 3. Planned fields

- `order_id`
- `customer_id`
- `customer_unique_id`
- `order_status`
- `order_purchase_timestamp`
- `item_count`
- `item_value`
- `freight_value`
- `payment_value`
- `review_score`

## 4. Aggregation and join rules

- Begin with the orders dataset as the order-level base.
- Join customers through `customer_id` to include `customer_unique_id`.
- Aggregate order items independently by `order_id` before joining.
- Calculate `item_count` as the number of order-item records.
- Calculate `item_value` as the sum of item prices per order.
- Calculate `freight_value` as the sum of freight charges per order.
- Aggregate payment records independently by `order_id`.
- Calculate `payment_value` as the sum of payment records per order.
- Aggregate reviews independently by `order_id` before joining.
- Calculate the arithmetic mean of all review scores per order, rounded to two decimal places.
- Preserve missing review scores for orders without reviews; do not invent a score.
- Never join raw one-to-many tables together before aggregation.

## 5. Financial interpretation

- Keep item value, freight value, and payment value separate.
- Do not assume payment totals equal item value plus freight.
- Do not silently modify or discard zero-valued payment records.
- Preserve the distinction between missing values and actual zero values.
- Document any financial reconciliation differences.

## 6. Validation requirements

- Output must contain exactly one row per order.
- `order_id` must be non-null and unique.
- Output order count must match the source orders count unless a documented
  transformation rule explains otherwise.
- Customer identifiers must map to the expected source records.
- Aggregated values must be checked against independently calculated source
  totals.
- Re-running the transformation with unchanged inputs must produce
  equivalent output.

## 7. Implementation status

Implemented:
- Transformation module: `src/transform_orders.py`
- Output: `data/processed/orders_analytics.csv`
- Output grain: one row per order.
- Output contains 99,441 rows and 10 columns.
- All 99,441 order IDs are unique and non-null.
- All customer identifiers successfully map to customer records.
- Item, freight, payment, and review tables are aggregated independently
  before joining to the order-level base.
- Orders without item, payment, or review records retain missing values.
- Item value, freight value, and payment value reconcile with their
  independently calculated source totals.
- Generated datasets under `data/processed/` are excluded from Git.

Automated tests:
- Full test suite: 34 tests passed.
- Transformation tests cover join fan-out prevention, preservation of
  missing child records, and source-total reconciliation.

Known missing records in the current output:
- 775 orders without item records.
- 1 order without payment records.
- 768 orders without review scores.

These missing values are preserved rather than silently replaced with zero.
