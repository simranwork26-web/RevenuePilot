"""Build product-category analytics from Olist source datasets."""

from math import isclose
from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw/olist")
PROCESSED_DATA_DIR = Path("data/processed")
OUTPUT_PATH = PROCESSED_DATA_DIR / "category_analytics.csv"


def build_category_analytics() -> pd.DataFrame:
    """Aggregate item and delivered-item metrics by product category."""
    orders = pd.read_csv(
        RAW_DATA_DIR / "olist_orders_dataset.csv",
        usecols=["order_id", "order_status"],
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

    if orders["order_id"].isna().any() or orders["order_id"].duplicated().any():
        raise ValueError("Orders must have unique, non-missing order IDs.")

    if products["product_id"].isna().any() or products["product_id"].duplicated().any():
        raise ValueError("Products must have unique, non-missing product IDs.")

    if items[["order_id", "order_item_id"]].isna().any().any():
        raise ValueError("Order items must have non-missing order and item IDs.")

    if items.duplicated(["order_id", "order_item_id"]).any():
        raise ValueError("Order item IDs must be unique within each order.")

    if translations["product_category_name"].duplicated().any():
        raise ValueError("Category translations must be unique by Portuguese category.")

    item_count_before_join = len(items)
    item_value_before_join = items["price"].sum()

    result = items.merge(
        orders,
        on="order_id",
        how="left",
        validate="many_to_one",
        indicator="_order_match",
    )

    if result["_order_match"].ne("both").any():
        raise ValueError("Some order items do not match a source order.")

    result = result.drop(columns="_order_match").merge(
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

    if len(result) != item_count_before_join:
        raise ValueError("Product joins changed the order-item row count.")

    if not isclose(
        float(result["price"].sum()),
        float(item_value_before_join),
        rel_tol=1e-12,
        abs_tol=1e-6,
    ):
        raise ValueError("Product joins changed the source item-value total.")

    result["category"] = result["product_category_name_english"].fillna(
        result["product_category_name"]
    )
    result["category"] = result["category"].fillna("unknown_category")
    result["is_delivered"] = result["order_status"].eq("delivered")

    result["delivered_item_count"] = result["is_delivered"].astype(int)
    result["delivered_item_value"] = result["price"].where(
        result["is_delivered"], 0
    )

    category_metrics = (
        result.groupby("category", dropna=False)
        .agg(
            item_count=("order_item_id", "size"),
            order_count=("order_id", "nunique"),
            delivered_item_count=("delivered_item_count", "sum"),
            delivered_order_count=(
                "order_id",
                lambda order_ids: order_ids[
                    result.loc[order_ids.index, "is_delivered"]
                ].nunique(),
            ),
            item_value_total=("price", "sum"),
            delivered_item_value=("delivered_item_value", "sum"),
        )
        .reset_index()
        .sort_values(
            ["delivered_item_value", "item_value_total", "category"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )

    if int(category_metrics["item_count"].sum()) != item_count_before_join:
        raise ValueError("Category item counts do not reconcile with source items.")

    if not isclose(
        float(category_metrics["item_value_total"].sum()),
        float(item_value_before_join),
        rel_tol=1e-12,
        abs_tol=1e-6,
    ):
        raise ValueError("Category item values do not reconcile with source items.")

    return category_metrics


def main() -> None:
    """Build and save the category-level analytical dataset."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    result = build_category_analytics()
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Output: {OUTPUT_PATH}")
    print(f"Categories: {len(result):,}")
    print(f"Order items: {result['item_count'].sum():,}")
    print(f"Item value total: {result['item_value_total'].sum():,.2f}")
    print(f"Delivered item value: {result['delivered_item_value'].sum():,.2f}")
    print("\nTop 10 categories by delivered item value:")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
