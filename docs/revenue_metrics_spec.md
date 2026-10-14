# RevenuePilot — Revenue Metrics Specification

## 1. Purpose

Define consistent business metrics for revenue analysis, order performance,
and customer purchasing behavior before implementing analytical code.

## 2. Source

Primary dataset: `data/processed/orders_analytics.csv`

Grain: one row per order, identified by `order_id`.

Customer-level repeat-purchase analysis must use `customer_unique_id`, not
`customer_id`, because different order records can represent the same
underlying customer.

## 3. Core metrics

### Order count

Count distinct `order_id` values in the selected population.

### Delivered order count

Count distinct orders where `order_status` is `delivered`.

### Item value

Sum available `item_value` values. Item value represents recorded item
prices, not automatically accounting revenue or profit.

### Delivered item value

Sum available `item_value` values only for orders with status `delivered`.

### Freight value

Sum available `freight_value` values. Keep freight separate from item value.

### Recorded payment value

Sum available `payment_value` values for the selected order population.
This is the value recorded in payment records and must not be assumed to equal
item value plus freight or accounting revenue.

### Average order item value

For the selected population, divide the sum of available `item_value` by the
number of orders in that population with item records. Exclude orders without
item records from the denominator and report that denominator explicitly.

### Average recorded payment per order

For the selected population, divide the sum of available `payment_value` by
the number of orders in that population with payment records. Report that
denominator explicitly.

### Repeat customers

Count distinct `customer_unique_id` values with more than one distinct order
in the specified analysis period. The analysis period and treatment of order
statuses must be stated for each result.

## 4. Status and missing-value rules

- Report status-specific metrics explicitly.
- Do not label all-status item value or payment value as delivered sales.
- Do not assume canceled or unavailable status means no payment was recorded.
- Preserve missing item, payment, and review values as missing.
- Do not silently replace missing values with zero.
- Do not fabricate refunds, profit, or accounting revenue from the available
  fields.
- Keep item value, freight value, and recorded payment value separate.

## 5. Known source observations

The initial order-status audit found:

- 96,478 delivered orders.
- 1,107 shipped orders.
- 625 canceled orders.
- 609 unavailable orders.
- 314 invoiced orders.
- 301 processing orders.
- 5 created orders.
- 2 approved orders.

The processed dataset has:
- 775 orders without item records.
- 1 order without payment records.
- 768 orders without review scores.

These are observed data-quality conditions, not values to silently impute.

## 6. Validation requirements

- Validate metric calculations with small controlled unit-test fixtures.
- Reconcile total item, freight, and payment values with their source totals.
- Check denominators and missing-value handling explicitly.
- Ensure joins do not multiply order-level measures.
- Keep the metric population and order-status filter explicit.

## 7. Initial verified results

Calculated from `data/processed/orders_analytics.csv`:

- Total orders: 99,441.
- Delivered orders: 96,478.
- Item value across all statuses: 13,591,643.70.
- Delivered item value: 13,221,498.11.
- Freight value across all statuses: 2,251,909.54.
- Recorded payment value across all statuses: 16,008,872.12.
- Average item value per order with item records: 137.75 across 98,666 orders.
- Average recorded payment per order with payment records: 160.99 across 99,440 orders.
- Repeat customers: 2,997, using distinct orders per `customer_unique_id`
  across all order statuses.

These are dataset-derived metrics, not audited accounting results.
Repeat-customer counts depend on the chosen order-status population.

## 8. Monthly trend analytics

Implemented in `src/monthly_analytics.py`.

Output: `data/processed/monthly_revenue_analytics.csv`

The output contains 26 consecutive calendar months from September 2016
through October 2018, including November 2016, which has no source orders.

Monthly fields:
- `month`
- `order_count`
- `delivered_order_count`
- `item_value_total`
- `delivered_item_value`
- `recorded_payment_value_total`
- `low_volume_month`

A month is flagged as low-volume when it has fewer than 100 orders. This is
a reporting flag, not a data-validity judgment.

Verified checks:
- 26 monthly rows and no duplicate months.
- Monthly order counts sum to 99,441.
- Monthly item value reconciles to 13,591,643.70.
- Monthly recorded payment value reconciles to 16,008,872.12.
- Five months are flagged as low-volume.

Interpretation limitations:
- September 2016, September 2018, and October 2018 have very few orders.
- October 2018 ends on October 17 in the source data.
- Missing November 2016 is represented with zero counts and values to make
  the calendar series continuous; this indicates no source orders were
  recorded for that month, not confirmed absence of all business activity.
- Monthly item value and payment value include all order statuses unless
  a status-specific metric is explicitly selected.
