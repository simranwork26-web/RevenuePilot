"""Calculate documented revenue and customer metrics from order-level data."""

from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/orders_analytics.csv")


def calculate_revenue_metrics(orders: pd.DataFrame) -> dict:
    """Calculate revenue metrics without changing the input DataFrame."""
    required_columns = {
        "order_id",
        "customer_unique_id",
        "order_status",
        "item_value",
        "freight_value",
        "payment_value",
    }
    missing_columns = required_columns - set(orders.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    if orders["order_id"].isna().any():
        raise ValueError("order_id contains missing values.")

    if orders["order_id"].duplicated().any():
        raise ValueError("order_id must be unique for order-level metrics.")

    if orders["customer_unique_id"].isna().any():
        raise ValueError("customer_unique_id contains missing values.")

    delivered = orders["order_status"].eq("delivered")
    item_records = orders["item_value"].notna()
    payment_records = orders["payment_value"].notna()

    customer_order_counts = (
        orders.groupby("customer_unique_id")["order_id"].nunique()
    )
    repeat_customer_count = int((customer_order_counts > 1).sum())

    item_value_total = float(orders["item_value"].sum())
    delivered_item_value = float(orders.loc[delivered, "item_value"].sum())
    freight_value_total = float(orders["freight_value"].sum())
    payment_value_total = float(orders["payment_value"].sum())

    item_order_count = int(item_records.sum())
    payment_order_count = int(payment_records.sum())

    return {
        "order_count": int(orders["order_id"].nunique()),
        "delivered_order_count": int(orders.loc[delivered, "order_id"].nunique()),
        "item_value_total": item_value_total,
        "delivered_item_value": delivered_item_value,
        "freight_value_total": freight_value_total,
        "recorded_payment_value_total": payment_value_total,
        "item_order_count": item_order_count,
        "average_item_value_per_order": (
            item_value_total / item_order_count if item_order_count else None
        ),
        "payment_order_count": payment_order_count,
        "average_recorded_payment_per_order": (
            payment_value_total / payment_order_count
            if payment_order_count
            else None
        ),
        "repeat_customer_count": repeat_customer_count,
        "repeat_customer_status_population": "all order statuses",
    }


def main() -> None:
    """Load the processed dataset and print the core metrics."""
    orders = pd.read_csv(INPUT_PATH)
    metrics = calculate_revenue_metrics(orders)

    print("RevenuePilot — Core Revenue Metrics")
    print(f"Source: {INPUT_PATH}")
    print(f"Order count: {metrics['order_count']:,}")
    print(f"Delivered order count: {metrics['delivered_order_count']:,}")
    print(f"Item value total: {metrics['item_value_total']:,.2f}")
    print(f"Delivered item value: {metrics['delivered_item_value']:,.2f}")
    print(f"Freight value total: {metrics['freight_value_total']:,.2f}")
    print(
        "Recorded payment value total: "
        f"{metrics['recorded_payment_value_total']:,.2f}"
    )
    print(
        "Average item value per order: "
        f"{metrics['average_item_value_per_order']:,.2f} "
        f"(denominator: {metrics['item_order_count']:,} orders)"
    )
    print(
        "Average recorded payment per order: "
        f"{metrics['average_recorded_payment_per_order']:,.2f} "
        f"(denominator: {metrics['payment_order_count']:,} orders)"
    )
    print(f"Repeat customers: {metrics['repeat_customer_count']:,}")
    print(
        "Repeat-customer population: "
        f"{metrics['repeat_customer_status_population']}"
    )


if __name__ == "__main__":
    main()
