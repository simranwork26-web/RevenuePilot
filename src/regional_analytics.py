"""Build state-level order and item-value analytics from Olist data."""

from math import isclose
from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw/olist")
PROCESSED_DATA_DIR = Path("data/processed")
OUTPUT_PATH = PROCESSED_DATA_DIR / "regional_analytics.csv"


def build_regional_analytics(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    items: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate orders, customers, and item values by customer state."""
    required_orders = {"order_id", "customer_id", "order_status"}
    required_customers = {
        "customer_id",
        "customer_unique_id",
        "customer_state",
    }
    required_items = {"order_id", "order_item_id", "price", "freight_value"}

    for name, frame, required in [
        ("orders", orders, required_orders),
        ("customers", customers, required_customers),
        ("items", items, required_items),
    ]:
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"{name} missing required columns: {', '.join(sorted(missing))}"
            )

    if orders["order_id"].isna().any() or orders["order_id"].duplicated().any():
        raise ValueError("Order IDs must be present and unique.")

    if orders["customer_id"].isna().any():
        raise ValueError("Orders contain missing customer IDs.")

    if customers["customer_id"].isna().any():
        raise ValueError("Customer IDs must not be missing.")

    if customers["customer_id"].duplicated().any():
        raise ValueError("Customer IDs must be unique in the customer dataset.")

    if customers["customer_unique_id"].isna().any():
        raise ValueError("Unique customer IDs must not be missing.")

    if customers["customer_state"].isna().any():
        raise ValueError("Customer states must not be missing.")

    if items[["order_id", "order_item_id"]].isna().any().any():
        raise ValueError("Order-item IDs must not be missing.")

    if items.duplicated(["order_id", "order_item_id"]).any():
        raise ValueError("Order-item IDs must be unique within each order.")

    if orders["customer_id"].isin(customers["customer_id"]).sum() != len(orders):
        raise ValueError("Some orders do not match a customer record.")

    if not items["order_id"].isin(orders["order_id"]).all():
        raise ValueError("Some order items do not match an order.")

    source_item_value = float(items["price"].sum())
    source_freight_value = float(items["freight_value"].sum())

    item_totals = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )

    result = orders.merge(
        customers[["customer_id", "customer_unique_id", "customer_state"]],
        on="customer_id",
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        item_totals,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    result[["item_value", "freight_value"]] = result[
        ["item_value", "freight_value"]
    ].fillna(0.0)

    result["is_delivered"] = result["order_status"].eq("delivered")
    result["delivered_item_value"] = result["item_value"].where(
        result["is_delivered"], 0.0
    )

    regional = (
        result.groupby("customer_state", as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            delivered_order_count=("is_delivered", "sum"),
            unique_customer_count=("customer_unique_id", "nunique"),
            item_value_total=("item_value", "sum"),
            delivered_item_value=("delivered_item_value", "sum"),
            freight_value_total=("freight_value", "sum"),
        )
    )

    regional["average_delivered_item_value_per_order"] = (
        regional["delivered_item_value"]
        .div(regional["delivered_order_count"].replace(0, pd.NA))
        .fillna(0.0)
    )

    regional = regional.sort_values(
        ["delivered_item_value", "order_count", "customer_state"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    if int(regional["order_count"].sum()) != len(orders):
        raise ValueError("Regional order counts do not reconcile with source orders.")

    if not isclose(
        float(regional["item_value_total"].sum()),
        source_item_value,
        rel_tol=1e-12,
        abs_tol=1e-6,
    ):
        raise ValueError("Regional item values do not reconcile with source items.")

    if not isclose(
        float(regional["freight_value_total"].sum()),
        source_freight_value,
        rel_tol=1e-12,
        abs_tol=1e-6,
    ):
        raise ValueError("Regional freight values do not reconcile with source items.")

    return regional


def main() -> None:
    """Build and save the regional analytical dataset."""
    orders = pd.read_csv(
        RAW_DATA_DIR / "olist_orders_dataset.csv",
        usecols=["order_id", "customer_id", "order_status"],
    )
    customers = pd.read_csv(
        RAW_DATA_DIR / "olist_customers_dataset.csv",
        usecols=["customer_id", "customer_unique_id", "customer_state"],
    )
    items = pd.read_csv(
        RAW_DATA_DIR / "olist_order_items_dataset.csv",
        usecols=["order_id", "order_item_id", "price", "freight_value"],
    )

    regional = build_regional_analytics(orders, customers, items)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    regional.to_csv(OUTPUT_PATH, index=False)

    print(f"Output: {OUTPUT_PATH}")
    print(f"States: {len(regional)}")
    print(f"Orders: {regional['order_count'].sum():,}")
    print(f"Delivered orders: {regional['delivered_order_count'].sum():,}")
    print(f"Item value total: {regional['item_value_total'].sum():,.2f}")
    print(f"Delivered item value: {regional['delivered_item_value'].sum():,.2f}")
    print(f"Freight value total: {regional['freight_value_total'].sum():,.2f}")
    print("\nTop 10 states by delivered item value:")
    print(regional.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
