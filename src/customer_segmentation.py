"""Build customer-level segmentation and retention metrics."""

from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/orders_analytics.csv")
OUTPUT_PATH = Path("data/processed/customer_segmentation.csv")
REFERENCE_DATE = pd.Timestamp("2018-10-18")
HIGH_VALUE_PERCENTILE = 0.90


def build_customer_segmentation(
    orders: pd.DataFrame,
    reference_date: pd.Timestamp = REFERENCE_DATE,
) -> pd.DataFrame:
    """Aggregate order records into reproducible customer-level metrics."""
    required = {
        "order_id",
        "customer_unique_id",
        "order_status",
        "order_purchase_timestamp",
        "item_value",
        "payment_value",
    }
    missing = required - set(orders.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    if orders["order_id"].isna().any() or orders["order_id"].duplicated().any():
        raise ValueError("order_id must be present and unique.")

    if orders["customer_unique_id"].isna().any():
        raise ValueError("customer_unique_id contains missing values.")

    result = orders.copy()
    result["order_purchase_timestamp"] = pd.to_datetime(
        result["order_purchase_timestamp"], errors="raise"
    )
    if result["order_purchase_timestamp"].isna().any():
        raise ValueError("Purchase timestamps contain missing values.")

    reference_date = pd.Timestamp(reference_date)
    if pd.isna(reference_date):
        raise ValueError("reference_date must be a valid timestamp.")

    if reference_date < result["order_purchase_timestamp"].max():
        raise ValueError("reference_date cannot precede the latest purchase.")

    result["is_delivered"] = result["order_status"].eq("delivered")
    result["delivered_item_value"] = result["item_value"].where(
        result["is_delivered"], 0.0
    )
    result["delivered_payment_value"] = result["payment_value"].where(
        result["is_delivered"], 0.0
    )

    customers = (
        result.groupby("customer_unique_id", as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            first_purchase=("order_purchase_timestamp", "min"),
            last_purchase=("order_purchase_timestamp", "max"),
            delivered_order_count=("is_delivered", "sum"),
            delivered_item_value=("delivered_item_value", "sum"),
            delivered_payment_value=("delivered_payment_value", "sum"),
        )
    )

    customers["recency_days"] = (
        reference_date.normalize()
        - customers["last_purchase"].dt.normalize()
    ).dt.days

    repeat_delivered = customers.loc[
        customers["order_count"].ge(2)
        & customers["delivered_order_count"].gt(0),
        "delivered_item_value",
    ]
    high_value_threshold = (
        float(repeat_delivered.quantile(HIGH_VALUE_PERCENTILE))
        if not repeat_delivered.empty
        else None
    )

    conditions = [
        customers["delivered_order_count"].eq(0),
        customers["order_count"].eq(1),
        customers["order_count"].ge(2)
        & customers["delivered_item_value"].ge(high_value_threshold)
        if high_value_threshold is not None
        else pd.Series(False, index=customers.index),
    ]
    choices = ["No delivered order", "One-time", "High-value repeat"]

    customers["segment"] = "Repeat"
    for condition, label in reversed(list(zip(conditions, choices))):
        customers.loc[condition, "segment"] = label

    customers["reference_date"] = reference_date.normalize()
    customers["high_value_threshold"] = high_value_threshold

    return customers.sort_values(
        ["segment", "delivered_item_value", "order_count"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def main() -> None:
    """Generate and summarize customer segmentation output."""
    orders = pd.read_csv(INPUT_PATH)
    customers = build_customer_segmentation(orders)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    customers.to_csv(OUTPUT_PATH, index=False)

    print(f"Output: {OUTPUT_PATH}")
    print(f"Reference date: {REFERENCE_DATE.date()}")
    print(f"Customers: {len(customers):,}")
    print(
        "High-value repeat threshold: "
        f"{customers['high_value_threshold'].iloc[0]:,.2f}"
    )
    print("\nCustomer segments:")
    print(
        customers.groupby("segment")
        .agg(
            customer_count=("customer_unique_id", "size"),
            delivered_item_value=("delivered_item_value", "sum"),
            median_recency_days=("recency_days", "median"),
        )
        .sort_values("customer_count", ascending=False)
        .to_string()
    )


if __name__ == "__main__":
    main()
