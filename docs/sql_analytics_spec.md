# SQL Analytics and Business Query Layer

## Objective

Milestone 8 adds PostgreSQL as the query layer for RevenuePilot. It loads processed analytics datasets into relational tables and provides reusable business queries.

## Technology

- PostgreSQL 16
- psycopg 3
- Python CSV parsing and type conversion
- Parameterized SQL statements
- pytest automated tests

## Database Tables

The `revenuepilot` database contains five analytics tables:

- `orders`: order-level customer, timestamp, item, freight, payment, and review fields.
- `category_analytics`: category-level order, item, and delivered item-value metrics.
- `customer_segmentation`: customer purchase frequency, recency, delivered value, and segment.
- `monthly_revenue_analytics`: monthly order counts, item values, recorded payment values, and low-volume flags.
- `regional_analytics`: state-level order, customer, freight, and delivered item-value metrics.

Primary keys, checks, and indexes are defined in `sql/schema.sql`.

## Loading Process

From the project root, run:

    .venv/bin/python -m src.load_postgres

The loader reads the five CSV files from `data/processed/`, validates their exact column order, converts values, and loads the tables in one database transaction.

Blank source values remain SQL NULL rather than being converted to zero. Only the five designated analytics tables are replaced.

The loader uses `REVENUEPILOT_DSN` when configured; otherwise, it connects to `dbname=revenuepilot`.

## Business Query Library

Run the queries with:

    psql -v ON_ERROR_STOP=1 -d revenuepilot -f sql/business_queries.sql

The library includes:
1. Monthly performance.
2. Top 10 product categories by delivered item value.
3. Top 10 states by delivered item value.
4. Customer segment distribution.
5. Repeat-customer summary.
6. Order-level data-quality checks.

## Reconciliation Results

| Metric | Result |
|---|---:|
| Total orders | 99,441 |
| Distinct order IDs | 99,441 |
| Delivered orders | 96,478 |
| Total item value across all statuses | 13,591,643.70 |
| Delivered item value | 13,221,498.11 |
| Freight value | 2,251,909.54 |
| Recorded payment value | 16,008,872.12 |
| Customers | 96,096 |
| Repeat customers | 2,997 |
| Repeat-customer percentage | 3.12% |
| Monthly records | 26 |

The SQL checks found no missing customer identifiers or purchase timestamps. Missing item values, payment values, and review scores remain preserved where present in the source data.

## Interpretation Notes

- Item value is not profit or audited accounting revenue.
- Recorded payment value and item value are different measures.
- Repeat-customer counts use the existing customer segmentation dataset and its recorded-order definition.
- The monthly dataset preserves the zero-order month.
- The data covers the source dataset period, not current business performance.

## Tests

Loader tests cover numeric conversion, decimal precision, missing-value preservation, date and timestamp parsing, boolean parsing, column validation, and row-level error reporting.

Run the complete test suite:

    .venv/bin/python -m pytest -q

Latest verified result: 82 tests passed.
