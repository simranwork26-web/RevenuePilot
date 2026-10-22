
"""Build monthly revenue-driver breakdowns by category and customer state."""

from math import isclose
from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw/olist")


def build_revenue_driver_drilldown(
    previous_month: str,
    current_month: str,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    translations: pd.DataFrame,
) -> dict:
    """Compare delivered item revenue by category and customer state."""
    for name, month in [
        ("previous_month", previous_month),
        ("current_month", current_month),
    ]:
        try:
            parsed = pd.Period(month, freq="M")
        except (ValueError, TypeError) as error:
            raise ValueError(f"{name} must use YYYY-MM format.") from error

        if str(parsed) != month:
            raise ValueError(f"{name} must use YYYY-MM format.")

    if pd.Period(current_month, freq="M") <= pd.Period(
        previous_month, freq="M"
    ):
        raise ValueError("current_month must be later than previous_month.")

    required = {
        "orders": (
            orders,
            {
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
            },
        ),
        "items": (
            items,
            {"order_id", "order_item_id", "product_id", "price"},
        ),
        "products": (
            products,
            {"product_id", "product_category_name"},
        ),
        "customers": (
            customers,
            {"customer_id", "customer_state"},
        ),
        "translations": (
            translations,
            {"product_category_name", "product_category_name_english"},
        ),
    }

    for name, (frame, columns) in required.items():
        missing = columns - set(frame.columns)
        if missing:
            raise ValueError(
                f"{name} missing required columns: {', '.join(sorted(missing))}"
            )

    if orders["order_id"].isna().any() or orders["order_id"].duplicated().any():
        raise ValueError("Orders must have unique, non-missing order IDs.")

    if customers["customer_id"].isna().any() or customers[
        "customer_id"
    ].duplicated().any():
        raise ValueError("Customers must have unique, non-missing customer IDs.")

    if products["product_id"].isna().any() or products[
        "product_id"
    ].duplicated().any():
        raise ValueError("Products must have unique, non-missing product IDs.")

    if items[["order_id", "order_item_id"]].isna().any().any():
        raise ValueError("Order items must have non-missing order and item IDs.")

    if items.duplicated(["order_id", "order_item_id"]).any():
        raise ValueError("Order item IDs must be unique within each order.")

    if translations["product_category_name"].duplicated().any():
        raise ValueError("Category translations must be unique.")

    if not items["order_id"].isin(orders["order_id"]).all():
        raise ValueError("Some order items do not match an order.")

    if not items["product_id"].isin(products["product_id"]).all():
        raise ValueError("Some order items do not match a product.")

    if not orders["customer_id"].isin(customers["customer_id"]).all():
        raise ValueError("Some orders do not match a customer.")

    source_item_value = float(items["price"].sum())

    result = items.merge(
        orders[
            [
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
            ]
        ],
        on="order_id",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        products,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        translations,
        on="product_category_name",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        customers[["customer_id", "customer_state"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    if len(result) != len(items):
        raise ValueError("Joins changed the order-item row count.")

    if not isclose(
        float(result["price"].sum()),
        source_item_value,
        rel_tol=1e-12,
        abs_tol=1e-6,
    ):
        raise ValueError("Joins changed the source item-value total.")

    result["month"] = (
        pd.to_datetime(
            result["order_purchase_timestamp"], errors="raise"
        )
        .dt.to_period("M")
        .astype(str)
    )

    available_months = set(result["month"].dropna())
    missing_months = {
        month
        for month in (previous_month, current_month)
        if month not in available_months
    }
    if missing_months:
        unavailable = ", ".join(sorted(missing_months))
        raise ValueError(
            f"One or both selected months are unavailable: {unavailable}."
        )

    result["category"] = result[
        "product_category_name_english"
    ].fillna(result["product_category_name"])
    result["category"] = result["category"].fillna("unknown_category")
    result["customer_state"] = result["customer_state"].fillna("unknown_state")
    result["delivered_revenue"] = result["price"].where(
        result["order_status"].eq("delivered"), 0.0
    )

    selected = result[
        result["month"].isin([previous_month, current_month])
    ].copy()

    def summarize(dimension: str) -> list[dict]:
        monthly = (
            selected.groupby([dimension, "month"], dropna=False)[
                "delivered_revenue"
            ]
            .sum()
            .unstack(fill_value=0.0)
        )

        for month in [previous_month, current_month]:
            if month not in monthly.columns:
                monthly[month] = 0.0

        monthly["previous_revenue"] = monthly[previous_month]
        monthly["current_revenue"] = monthly[current_month]
        monthly["revenue_change"] = (
            monthly["current_revenue"] - monthly["previous_revenue"]
        )

        monthly = monthly.sort_values(
            "revenue_change", ascending=False
        )

        return [
            {
                dimension: str(segment),
                "previous_revenue": round(float(row["previous_revenue"]), 2),
                "current_revenue": round(float(row["current_revenue"]), 2),
                "revenue_change": round(float(row["revenue_change"]), 2),
            }
            for segment, row in monthly.iterrows()
        ]

    category_drivers = summarize("category")
    regional_drivers = summarize("customer_state")

    previous_total = float(
        selected.loc[
            selected["month"].eq(previous_month), "delivered_revenue"
        ].sum()
    )
    current_total = float(
        selected.loc[
            selected["month"].eq(current_month), "delivered_revenue"
        ].sum()
    )

    for label, drivers in [
        ("category", category_drivers),
        ("regional", regional_drivers),
    ]:
        driver_total = sum(row["revenue_change"] for row in drivers)
        if not isclose(
            driver_total,
            current_total - previous_total,
            rel_tol=1e-9,
            abs_tol=0.02,
        ):
            raise ValueError(
                f"{label.title()} revenue changes do not reconcile "
                "to the overall revenue change."
            )

    return {
        "previous_month": previous_month,
        "current_month": current_month,
        "previous_revenue": round(previous_total, 2),
        "current_revenue": round(current_total, 2),
        "revenue_change": round(current_total - previous_total, 2),
        "category_drivers": category_drivers,
        "regional_drivers": regional_drivers,
    }


def load_revenue_driver_drilldown(
    previous_month: str, current_month: str
) -> dict:
    """Load Olist source files and build the monthly driver breakdown."""
    orders = pd.read_csv(
        RAW_DATA_DIR / "olist_orders_dataset.csv",
        usecols=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
    )
    items = pd.read_csv(
        RAW_DATA_DIR / "olist_order_items_dataset.csv",
        usecols=["order_id", "order_item_id", "product_id", "price"],
    )
    products = pd.read_csv(
        RAW_DATA_DIR / "olist_products_dataset.csv",
        usecols=["product_id", "product_category_name"],
    )
    customers = pd.read_csv(
        RAW_DATA_DIR / "olist_customers_dataset.csv",
        usecols=["customer_id", "customer_state"],
    )
    translations = pd.read_csv(
        RAW_DATA_DIR / "product_category_name_translation.csv",
    )

    return build_revenue_driver_drilldown(
        previous_month,
        current_month,
        orders,
        items,
        products,
        customers,
        translations,
    )
