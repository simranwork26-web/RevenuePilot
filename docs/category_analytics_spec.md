# Product Category Analytics Specification

## 1. Purpose

Produce category-level metrics from the Olist Brazilian E-Commerce dataset
to compare item value, delivered item value, item counts, and order counts.

## 2. Source and output

Sources:
- `data/raw/olist/olist_orders_dataset.csv`
- `data/raw/olist/olist_order_items_dataset.csv`
- `data/raw/olist/olist_products_dataset.csv`
- `data/raw/olist/product_category_name_translation.csv`

Implementation: `src/category_analytics.py`

Output: `data/processed/category_analytics.csv`

The generated output is excluded from Git and can be regenerated with:

`.venv/bin/python -m src.category_analytics`

## 3. Grain and joins

The source grain is one row per order item, identified by
`(order_id, order_item_id)`.

Order items are joined to orders, products, and category translations.
The joins validate expected many-to-one relationships and must preserve
the source order-item row count and item-value total.

## 4. Metric definitions

- `item_count`: number of order-item rows in the category.
- `order_count`: distinct orders represented in the category.
- `delivered_item_count`: number of items whose order status is delivered.
- `delivered_order_count`: distinct delivered orders represented in the category.
- `item_value_total`: sum of item prices across all order statuses.
- `delivered_item_value`: sum of item prices for delivered orders.

An order may contain items from multiple categories. Therefore, summing
category-level order counts can exceed the number of unique source orders.
The same applies to delivered order counts.

Item value is not profit, margin, or audited accounting revenue. Freight
and recorded payment values are not included in these category item-value
metrics.

## 5. Category labels and missing data

Use the English translation when available. Otherwise, retain the original
Portuguese category name. Items without a matching product record are
assigned to `unknown_category`.

Untranslated category labels are retained rather than dropped.

## 6. Validation requirements

- Order IDs must be present and unique in the orders source.
- Product IDs must be present and unique in the products source.
- Order-item IDs must be present and unique within each order.
- Category translations must be unique by Portuguese category.
- Every order item must match a source order.
- Joins must preserve order-item row count and item-value total.
- Aggregated category item counts and item values must reconcile with
  the source order-item table.

## 7. Verified dataset results

- Category labels: 74.
- Source order items: 112,650.
- All-status item value: 13,591,643.70.
- Delivered item value: 13,221,498.11.
- Items assigned to `unknown_category`: 1,603.
- Item value assigned to `unknown_category`: 179,535.28.
- Delivered item value assigned to `unknown_category`: 170,726.63.

The 1,627 items without an English category consist of 1,603 items without
a matching product record, 15 items in `portateis_cozinha_e_preparadores_de_alimentos`,
and 9 items in `pc_gamer`.

## 8. Automated tests

The category analytics test suite covers:
- Aggregation without join fanout.
- Preservation of untranslated and unknown categories.
- Reconciliation with source item totals.
- Rejection of duplicate product IDs.
- Rejection of duplicate order-item IDs.
- Rejection of order items without matching orders.
