"""Load validated processed CSV datasets into PostgreSQL."""

import csv
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg
from psycopg import sql


DATA_DIR = Path("data/processed")
DATABASE_NAME = "revenuepilot"

TABLES = {
    "orders": {
        "file": "orders_analytics.csv",
        "columns": [
            "order_id",
            "customer_id",
            "customer_unique_id",
            "order_status",
            "order_purchase_timestamp",
            "item_count",
            "item_value",
            "freight_value",
            "payment_value",
            "review_score",
        ],
        "dates": {"order_purchase_timestamp": "timestamp"},
        "integers": {"item_count"},
        "decimals": {
            "item_value",
            "freight_value",
            "payment_value",
            "review_score",
        },
    },
    "category_analytics": {
        "file": "category_analytics.csv",
        "columns": [
            "category",
            "item_count",
            "order_count",
            "delivered_item_count",
            "delivered_order_count",
            "item_value_total",
            "delivered_item_value",
        ],
        "integers": {
            "item_count",
            "order_count",
            "delivered_item_count",
            "delivered_order_count",
        },
        "decimals": {"item_value_total", "delivered_item_value"},
    },
    "customer_segmentation": {
        "file": "customer_segmentation.csv",
        "columns": [
            "customer_unique_id",
            "order_count",
            "first_purchase",
            "last_purchase",
            "delivered_order_count",
            "delivered_item_value",
            "delivered_payment_value",
            "recency_days",
            "segment",
            "reference_date",
            "high_value_threshold",
        ],
        "dates": {
            "first_purchase": "timestamp",
            "last_purchase": "timestamp",
            "reference_date": "date",
        },
        "integers": {
            "order_count",
            "delivered_order_count",
            "recency_days",
        },
        "decimals": {
            "delivered_item_value",
            "delivered_payment_value",
            "high_value_threshold",
        },
    },
    "monthly_revenue_analytics": {
        "file": "monthly_revenue_analytics.csv",
        "columns": [
            "month",
            "order_count",
            "delivered_order_count",
            "item_value_total",
            "delivered_item_value",
            "recorded_payment_value_total",
            "low_volume_month",
        ],
        "dates": {"month": "date"},
        "integers": {"order_count", "delivered_order_count"},
        "decimals": {
            "item_value_total",
            "delivered_item_value",
            "recorded_payment_value_total",
        },
        "booleans": {"low_volume_month"},
    },
    "regional_analytics": {
        "file": "regional_analytics.csv",
        "columns": [
            "customer_state",
            "order_count",
            "delivered_order_count",
            "unique_customer_count",
            "item_value_total",
            "delivered_item_value",
            "freight_value_total",
            "average_delivered_item_value_per_order",
        ],
        "integers": {
            "order_count",
            "delivered_order_count",
            "unique_customer_count",
        },
        "decimals": {
            "item_value_total",
            "delivered_item_value",
            "freight_value_total",
            "average_delivered_item_value_per_order",
        },
    },
}


def parse_value(column: str, raw_value: str, config: dict):
    """Convert a CSV field to a database-compatible Python value."""
    if raw_value is None or raw_value.strip() == "":
        return None

    value = raw_value.strip()

    if column in config.get("integers", set()):
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(
                f"Expected numeric value for {column}: {raw_value!r}"
            ) from error
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError(f"Expected integer for {column}: {raw_value!r}")
        return int(number)

    if column in config.get("decimals", set()):
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(
                f"Expected numeric value for {column}: {raw_value!r}"
            ) from error
        if not number.is_finite():
            raise ValueError(f"Expected finite decimal for {column}: {raw_value!r}")
        return number

    date_type = config.get("dates", {}).get(column)
    if date_type == "timestamp":
        return datetime.fromisoformat(value)
    if date_type == "date":
        return date.fromisoformat(value)

    if column in config.get("booleans", set()):
        normalized = value.lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        raise ValueError(f"Expected boolean for {column}: {raw_value!r}")

    return value


def read_dataset(table: str, config: dict) -> list[tuple]:
    """Read and convert a CSV after verifying its exact column set."""
    path = DATA_DIR / config["file"]
    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != config["columns"]:
            raise ValueError(
                f"Unexpected columns in {path}: {reader.fieldnames!r}"
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                converted = tuple(
                    parse_value(column, row[column], config)
                    for column in config["columns"]
                )
            except (ValueError, ArithmeticError) as error:
                raise ValueError(
                    f"Invalid data in {path}, CSV row {row_number}: {error}"
                ) from error

            rows.append(converted)

    return rows


def load_all(connection) -> dict[str, int]:
    """Replace the five dedicated analytics tables in one transaction."""
    expected_counts = {}

    with connection.transaction():
        for table, config in TABLES.items():
            rows = read_dataset(table, config)
            columns = config["columns"]

            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DELETE FROM {}").format(sql.Identifier(table))
                )

                insert_statement = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({})"
                ).format(
                    sql.Identifier(table),
                    sql.SQL(", ").join(
                        sql.Identifier(column) for column in columns
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder() for _ in columns
                    ),
                )

                if rows:
                    cursor.executemany(insert_statement, rows)

                cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table)
                    )
                )
                actual_count = cursor.fetchone()[0]

            if actual_count != len(rows):
                raise RuntimeError(
                    f"Row count mismatch for {table}: "
                    f"expected {len(rows)}, got {actual_count}"
                )

            expected_counts[table] = actual_count

    return expected_counts


def main() -> None:
    """Load all processed analytics datasets."""
    dsn = os.environ.get("REVENUEPILOT_DSN", "dbname=revenuepilot")

    with psycopg.connect(dsn) as connection:
        counts = load_all(connection)

    print("PostgreSQL load completed.")
    for table, count in counts.items():
        print(f"{table}: {count:,} rows")


if __name__ == "__main__":
    main()
