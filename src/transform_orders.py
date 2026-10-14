"""Build an order-level analytical dataset from the Olist source CSV files."""

from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw/olist")
PROCESSED_DATA_DIR = Path("data/processed")
OUTPUT_PATH = PROCESSED_DATA_DIR / "orders_analytics.csv"


def build_orders_analytics() -> pd.DataFrame:
    """Aggregate child tables before joining them to the order-level base."""
    orders = pd.read_csv(
        RAW_DATA_DIR / "olist_orders_dataset.csv",
        usecols=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
    )

    customers = pd.read_csv(
        RAW_DATA_DIR / "olist_customers_dataset.csv",
        usecols=["customer_id", "customer_unique_id"],
    )

    items = pd.read_csv(
        RAW_DATA_DIR / "olist_order_items_dataset.csv",
        usecols=["order_id", "price", "freight_value"],
    )

    payments = pd.read_csv(
        RAW_DATA_DIR / "olist_order_payments_dataset.csv",
        usecols=["order_id", "payment_value"],
    )

    reviews = pd.read_csv(
        RAW_DATA_DIR / "olist_order_reviews_dataset.csv",
        usecols=["order_id", "review_score"],
    )

    item_aggregates = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_count=("order_id", "size"),
            item_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )

    payment_aggregates = (
        payments.groupby("order_id", as_index=False)
        .agg(payment_value=("payment_value", "sum"))
    )

    review_aggregates = (
        reviews.groupby("order_id", as_index=False)
        .agg(review_score=("review_score", "mean"))
    )

    review_aggregates["review_score"] = review_aggregates[
        "review_score"
    ].round(2)

    result = orders.merge(
        customers,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        item_aggregates,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        payment_aggregates,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        review_aggregates,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    expected_columns = [
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
    ]

    result = result[expected_columns]

    if result["order_id"].isna().any():
        raise ValueError("Output contains missing order_id values.")

    if result["order_id"].duplicated().any():
        raise ValueError("Output contains duplicate order_id values.")

    if len(result) != len(orders):
        raise ValueError(
            f"Output row count {len(result):,} does not match "
            f"source orders {len(orders):,}."
        )

    if result["customer_unique_id"].isna().any():
        raise ValueError("Some orders have no matching customer record.")

    return result


def main() -> None:
    """Build and save the processed order-level dataset."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    result = build_orders_analytics()
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Output: {OUTPUT_PATH}")
    print(f"Rows: {len(result):,}")
    print(f"Columns: {len(result.columns)}")
    print(f"Unique orders: {result['order_id'].nunique():,}")
    print(f"Orders without review scores: {result['review_score'].isna().sum():,}")


if __name__ == "__main__":
    main()
