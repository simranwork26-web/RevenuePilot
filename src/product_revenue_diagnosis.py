"""Build product-level revenue diagnosis across two months."""

from math import isclose
from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw/olist")


def build_product_revenue_diagnosis(
    previous_month: str,
    current_month: str,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    translations: pd.DataFrame,
) -> dict:
    """Compare delivered product revenue, orders, items, and average price."""

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
            {"order_id", "order_status", "order_purchase_timestamp"},
        ),
        "items": (
            items,
            {"order_id", "order_item_id", "product_id", "price"},
        ),
        "products": (
            products,
            {"product_id", "product_category_name"},
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
                f"{name} missing required columns: "
                f"{', '.join(sorted(missing))}"
            )

    if orders["order_id"].isna().any() or orders["order_id"].duplicated().any():
        raise ValueError("Orders must have unique, non-missing order IDs.")

    if products["product_id"].isna().any() or products[
        "product_id"
    ].duplicated().any():
        raise ValueError("Products must have unique, non-missing product IDs.")

    if items[["order_id", "order_item_id", "product_id"]].isna().any().any():
        raise ValueError("Order items must have non-missing IDs.")

    if items.duplicated(["order_id", "order_item_id"]).any():
        raise ValueError("Order item IDs must be unique within each order.")

    if translations["product_category_name"].duplicated().any():
        raise ValueError("Category translations must be unique.")

    if not items["order_id"].isin(orders["order_id"]).all():
        raise ValueError("Some order items do not match an order.")

    if not items["product_id"].isin(products["product_id"]).all():
        raise ValueError("Some order items do not match a product.")

    items = items.copy()
    items["price"] = pd.to_numeric(items["price"], errors="raise")

    source_item_value = float(items["price"].sum())

    result = items.merge(
        orders[["order_id", "order_status", "order_purchase_timestamp"]],
        on="order_id",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        products[["product_id", "product_category_name"]],
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

    result["category"] = (
        result["product_category_name_english"]
        .fillna(result["product_category_name"])
        .fillna("unknown_category")
    )

    result["delivered"] = result["order_status"].eq("delivered")

    selected = result[
        result["month"].isin([previous_month, current_month])
    ].copy()

    delivered = selected[selected["delivered"]].copy()

    if delivered.empty:
        raise ValueError("No delivered product records in selected months.")

    monthly = (
        delivered.groupby(
            ["product_id", "category", "month"],
            dropna=False,
        )
        .agg(
            revenue=("price", "sum"),
            items=("order_item_id", "count"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
    )

    product_catalog = selected[
        ["product_id", "category"]
    ].drop_duplicates()

    if product_catalog["product_id"].duplicated().any():
        raise ValueError("Products have inconsistent category assignments.")

    product_catalog = product_catalog.set_index("product_id")

    def metric(metric_name: str, month: str) -> pd.Series:
        values = (
            monthly[monthly["month"].eq(month)]
            .set_index("product_id")[metric_name]
        )
        return values.reindex(product_catalog.index, fill_value=0)

    product_results = product_catalog.copy()

    for metric_name in ["revenue", "items", "orders"]:
        product_results[f"previous_{metric_name}"] = metric(
            metric_name, previous_month
        )
        product_results[f"current_{metric_name}"] = metric(
            metric_name, current_month
        )

    product_results["revenue_change"] = (
        product_results["current_revenue"]
        - product_results["previous_revenue"]
    )

    product_results["revenue_change_pct"] = [
        round((current - previous) / previous * 100, 2)
        if previous > 0 else None
        for previous, current in zip(
            product_results["previous_revenue"],
            product_results["current_revenue"],
        )
    ]

    for period in ["previous", "current"]:
        product_results[f"{period}_avg_item_price"] = (
            product_results[f"{period}_revenue"]
            / product_results[f"{period}_items"].replace(0, pd.NA)
        ).fillna(0)

    product_results = product_results.sort_values("revenue_change")

    product_drivers = [
        {
            "product_id": str(product_id),
            "category": str(row["category"]),
            "previous_revenue": round(float(row["previous_revenue"]), 2),
            "current_revenue": round(float(row["current_revenue"]), 2),
            "revenue_change": round(float(row["revenue_change"]), 2),
            "revenue_change_pct": row["revenue_change_pct"],
            "previous_orders": int(row["previous_orders"]),
            "current_orders": int(row["current_orders"]),
            "previous_items": int(row["previous_items"]),
            "current_items": int(row["current_items"]),
            "previous_avg_item_price": round(
                float(row["previous_avg_item_price"]), 2
            ),
            "current_avg_item_price": round(
                float(row["current_avg_item_price"]), 2
            ),
        }
        for product_id, row in product_results.iterrows()
    ]

    category_changes = (
        product_results.groupby("category")["revenue_change"]
        .sum()
        .sort_values()
    )

    total_category_decline = abs(
        float(category_changes[category_changes < 0].sum())
    )

    category_drivers = [
        {
            "category": str(category),
            "revenue_change": round(float(change), 2),
            "decline_contribution_pct": (
                round(abs(float(change)) / total_category_decline * 100, 2)
                if change < 0 and total_category_decline > 0
                else None
            ),
        }
        for category, change in category_changes.items()
    ]

    previous_total = float(
        delivered.loc[
            delivered["month"].eq(previous_month), "price"
        ].sum()
    )
    current_total = float(
        delivered.loc[
            delivered["month"].eq(current_month), "price"
        ].sum()
    )

    product_change_total = sum(
        row["revenue_change"] for row in product_drivers
    )

    if not isclose(
        product_change_total,
        current_total - previous_total,
        rel_tol=1e-9,
        abs_tol=0.02,
    ):
        raise ValueError(
            "Product revenue changes do not reconcile to total revenue change."
        )

    return {
        "previous_month": previous_month,
        "current_month": current_month,
        "previous_revenue": round(previous_total, 2),
        "current_revenue": round(current_total, 2),
        "revenue_change": round(current_total - previous_total, 2),
        "product_count": len(product_drivers),
        "product_drivers": product_drivers,
        "category_drivers": category_drivers,
    }


def load_product_revenue_diagnosis(
    previous_month: str,
    current_month: str,
) -> dict:
    """Load Olist source files and build product-level diagnosis."""

    orders = pd.read_csv(
        RAW_DATA_DIR / "olist_orders_dataset.csv",
        usecols=[
            "order_id",
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

    translations = pd.read_csv(
        RAW_DATA_DIR / "product_category_name_translation.csv",
    )

    return build_product_revenue_diagnosis(
        previous_month,
        current_month,
        orders,
        items,
        products,
        translations,
    )
