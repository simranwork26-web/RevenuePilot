# Regional Analytics Specification

## 1. Purpose

Compare order activity, delivered item value, customer counts, and freight
value across Brazilian states using the Olist e-commerce dataset.

## 2. Sources and output

Sources:
- `data/raw/olist/olist_orders_dataset.csv`
- `data/raw/olist/olist_customers_dataset.csv`
- `data/raw/olist/olist_order_items_dataset.csv`

Implementation: `src/regional_analytics.py`

Output: `data/processed/regional_analytics.csv`

Regenerate the output with:

`.venv/bin/python -m src.regional_analytics`

## 3. Grain and joins

The output contains one row per customer state.

Order items are aggregated by order ID before being joined to orders and
customer records. This avoids multiplying order counts when an order
contains multiple items.

Every order must match one customer record, and every order item must
match a source order.

## 4. Metric definitions

- `order_count`: number of distinct orders assigned to the state.
- `delivered_order_count`: number of orders with status `delivered`.
- `unique_customer_count`: distinct customer identities represented in
  the state's orders, using `customer_unique_id`.
- `item_value_total`: sum of item prices for all order statuses.
- `delivered_item_value`: sum of item prices for delivered orders.
- `freight_value_total`: sum of freight values for all order statuses.
- `average_delivered_item_value_per_order`: delivered item value divided
  by delivered order count; zero when the state has no delivered orders.

State attribution uses the customer's recorded state, not the seller's
state or the delivery destination's independently inferred region.

## 5. Validation requirements

- Required columns must be present.
- Order IDs must be present and unique.
- Customer IDs must be present and unique in the customer dataset.
- Customer identity and state values must not be missing.
- Order-item IDs must be present and unique within each order.
- Every order must match a customer record.
- Every order item must match a source order.
- Regional order counts must reconcile with source orders.
- Regional item and freight totals must reconcile with source order items.

## 6. Verified dataset results

- States: 27.
- Orders: 99,441.
- Delivered orders: 96,478.
- All-status item value: 13,591,643.70.
- Delivered item value: 13,221,498.11.
- Freight value: 2,251,909.54.

The highest delivered item value is in São Paulo (SP), at 5,067,633.16,
followed by Rio de Janeiro (RJ), at 1,759,651.13, and Minas Gerais (MG),
at 1,552,481.83.

Item value is not profit, margin, or audited accounting revenue.
