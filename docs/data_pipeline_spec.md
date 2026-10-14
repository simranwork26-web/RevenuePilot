# RevenuePilot — Data Pipeline Specification

## 1. Purpose

Build a reproducible data pipeline that ingests the Olist Brazilian E-Commerce dataset, validates its structure and quality, and produces reliable processed datasets for SQL analytics, Power BI dashboards, and forecasting.

## 2. Source data

Source directory: `data/raw/olist/`

Expected CSV files:

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

## 3. Pipeline principles

- Never overwrite or modify raw source files.
- Make transformations deterministic and repeatable.
- Validate required columns before processing.
- Validate primary keys and relationships between tables.
- Preserve legitimate missing values instead of inventing replacements.
- Record validation failures and warnings.
- Keep product prices, freight charges, and payment values as separate measures.
- Prevent one-to-many joins from silently inflating business metrics.
- Document metric definitions and transformation assumptions.

## 4. Initial data-quality rules

- Orders must have unique, non-empty `order_id` values.
- Customer records must have unique, non-empty `customer_id` values.
- Product records must have unique, non-empty `product_id` values.
- Order-item references to orders, products, and sellers must be checked.
- Order references to customers must be checked.
- Purchase timestamps must parse successfully.
- Missing delivery timestamps must not be fabricated.
- Financial fields must be checked for missing, non-numeric, zero, and negative values.
- Missing product categories and untranslated categories must be handled explicitly.
- Payment totals must not be assumed to equal item value plus freight.

## 5. Output locations

- Source files: `data/raw/`
- Processed datasets: `data/processed/`
- Pipeline source code: `src/`
- Automated tests: `tests/`
- Documentation and validation reports: `docs/`

## 6. Completion criteria

The pipeline must be repeatable, validate its inputs, report actionable errors, preserve source data, and produce outputs that can be independently checked before downstream analytics use them.

## 7. Implemented validation checks

Implemented in `src/ingest.py`, `src/dataset_manifest.py`, and
`src/validate_dataset.py`:

- Checks that all nine expected CSV files exist.
- Checks required columns and expected row counts.
- Checks configured unique columns for duplicate values.
- Validates required foreign-key relationships.
- Validates optional product-category references against approved exceptions.
- Parses configured timestamp columns and rejects invalid timestamps.
- Rejects blank values in required timestamp columns while allowing configured optional blanks.
- Validates configured numeric columns for blank, non-numeric, non-finite, below-minimum, disallowed-zero, and non-integer values.
- Reports configurable zero-value warnings for payment values and payment installments without failing validation solely because of those warnings.
- Returns a failing exit status when dataset validation fails.

### Known category exceptions

Two product categories are explicitly allowed even though they are absent
from the translation table:

- `pc_gamer`
- `portateis_cozinha_e_preparadores_de_alimentos`

These values are reported rather than silently replaced or discarded.

### Verified baseline

- Expected CSV files: 9
- Total source rows: 1,550,922
- Required foreign-key relationships: 6
- Automated tests: 34 passing at the completion of Milestone 3
- Timestamp validation: implemented and covered by unit and validator-level tests
- Numeric validation: implemented and covered by unit tests
- Actual dataset validation: 9 of 9 datasets passed
- Zero-value warnings: 9 payment values and 2 payment-installment records

Rerun the checks after changes to the pipeline or source data.

### Verification commands

Run automated tests:

    .venv/bin/python -m unittest discover -s tests -v

Validate the actual source datasets:

    .venv/bin/python -m src.validate_dataset

Check pending Git changes for whitespace errors:

    git diff --check

## 8. Remaining pipeline work

The following requirements are not yet implemented or fully tested:

- Investigating the nine zero-valued payment records and two zero-installment
  records flagged by the current validation run.
- Extending processed datasets for additional analytical use cases.
- Generating a persistent validation report.
- Documenting and testing metric definitions before downstream SQL analytics begin.
