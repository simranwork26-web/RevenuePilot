"""Build monthly order and financial trend metrics."""

from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/orders_analytics.csv")
OUTPUT_PATH = Path("data/processed/monthly_revenue_analytics.csv")
LOW_VOLUME_THRESHOLD = 100


def build_monthly_analytics(orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate order-level metrics by purchase month."""
    required_columns = {
        "order_id",
        "order_purchase_timestamp",
        "order_status",
        "item_value",
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
        raise ValueError("order_id must be unique for monthly analytics.")

    result = orders.copy()
    result["order_purchase_timestamp"] = pd.to_datetime(
        result["order_purchase_timestamp"], errors="raise"
    )

    if result["order_purchase_timestamp"].isna().any():
        raise ValueError("Purchase timestamps contain missing values.")

    result["month"] = (
        result["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    )
    result["is_delivered"] = result["order_status"].eq("delivered")

    monthly = result.groupby("month").agg(
        order_count=("order_id", "nunique"),
        delivered_order_count=("is_delivered", "sum"),
        item_value_total=("item_value", "sum"),
        delivered_item_value=(
            "item_value",
            lambda values: values[result.loc[values.index, "is_delivered"]].sum(),
        ),
        recorded_payment_value_total=("payment_value", "sum"),
    )

    full_months = pd.date_range(
        start=monthly.index.min(),
        end=monthly.index.max(),
        freq="MS",
    )
    monthly = monthly.reindex(full_months)
    monthly.index.name = "month"

    count_columns = ["order_count", "delivered_order_count"]
    monthly[count_columns] = monthly[count_columns].fillna(0).astype(int)

    for column in [
        "item_value_total",
        "delivered_item_value",
        "recorded_payment_value_total",
    ]:
        monthly.loc[monthly["order_count"] == 0, column] = 0.0

    monthly["low_volume_month"] = (
        monthly["order_count"] < LOW_VOLUME_THRESHOLD
    )

    return monthly.reset_index()


def main() -> None:
    """Build and save monthly metrics from the processed order dataset."""
    orders = pd.read_csv(INPUT_PATH)
    monthly = build_monthly_analytics(orders)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(OUTPUT_PATH, index=False)

    print(f"Output: {OUTPUT_PATH}")
    print(f"Months: {len(monthly)}")
    print(f"Low-volume months: {int(monthly['low_volume_month'].sum())}")
    print(monthly.to_string(index=False))


if __name__ == "__main__":
    main()
