from __future__ import annotations

from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "olist"

ORDER_COLUMNS = {
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
}

ITEM_COLUMNS = {"order_id", "price"}

CUSTOMER_COLUMNS = {
    "customer_id",
    "customer_unique_id",
    "customer_state",
}


def _validate_months(previous_month: str, current_month: str) -> None:
    for month in (previous_month, current_month):
        try:
            parsed = pd.Period(month, freq="M")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Months must use YYYY-MM format."
            ) from exc

        if str(parsed) != month:
            raise ValueError("Months must use YYYY-MM format.")

    if pd.Period(current_month, freq="M") <= pd.Period(
        previous_month, freq="M"
    ):
        raise ValueError("Current month must be later than previous month.")


def _validate_inputs(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    customers: pd.DataFrame,
) -> None:
    for name, frame, required in (
        ("orders", orders, ORDER_COLUMNS),
        ("items", items, ITEM_COLUMNS),
        ("customers", customers, CUSTOMER_COLUMNS),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"{name} is missing required columns: {sorted(missing)}"
            )

    for name, frame, key in (
        ("orders", orders, "order_id"),
        ("customers", customers, "customer_id"),
    ):
        if frame[key].isna().any():
            raise ValueError(f"{name} contains missing {key} values.")
        if frame[key].duplicated().any():
            raise ValueError(f"{name} contains duplicate {key} values.")

    if items[["order_id"]].isna().any().any():
        raise ValueError("items contains missing order_id values.")

    if customers["customer_unique_id"].isna().any():
        raise ValueError("customers contains missing customer_unique_id values.")

    if not pd.api.types.is_numeric_dtype(items["price"]):
        raise ValueError("items price must be numeric.")

    if items["price"].isna().any() or (items["price"] < 0).any():
        raise ValueError("items price must contain valid non-negative values.")


def _prepare_delivered_data(
    previous_month: str,
    current_month: str,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    _validate_months(previous_month, current_month)
    _validate_inputs(orders, items, customers)

    order_data = orders.copy()
    order_data["order_purchase_timestamp"] = pd.to_datetime(
        order_data["order_purchase_timestamp"],
        errors="coerce",
    )
    order_data = order_data.dropna(subset=["order_purchase_timestamp"])
    order_data["month"] = (
        order_data["order_purchase_timestamp"].dt.to_period("M").astype(str)
    )

    relevant_months = {previous_month, current_month}
    order_data = order_data[
        order_data["month"].isin(relevant_months)
        & order_data["order_status"].eq("delivered")
    ].copy()

    merged = items.merge(
        order_data,
        on="order_id",
        how="inner",
        validate="many_to_one",
    )

    merged = merged.merge(
        customers[
            ["customer_id", "customer_unique_id", "customer_state"]
        ],
        on="customer_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    if merged["_merge"].ne("both").any():
        raise ValueError("Some delivered orders have no matching customer.")

    merged = merged.drop(columns="_merge")

    if merged["customer_state"].isna().any():
        raise ValueError("Customer state is missing for delivered orders.")

    return merged


def _build_regional_diagnosis(
    data: pd.DataFrame,
    previous_month: str,
    current_month: str,
    overall_revenue_change: float,
) -> list[dict]:
    monthly = (
        data.groupby(["customer_state", "month"])
        .agg(
            revenue=("price", "sum"),
            delivered_orders=("order_id", "nunique"),
            customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
    )

    states = sorted(data["customer_state"].dropna().unique())
    results = []

    for state in states:
        state_data = monthly[monthly["customer_state"].eq(state)]
        previous = state_data[state_data["month"].eq(previous_month)]
        current = state_data[state_data["month"].eq(current_month)]

        previous_revenue = (
            float(previous["revenue"].iloc[0]) if not previous.empty else 0.0
        )
        current_revenue = (
            float(current["revenue"].iloc[0]) if not current.empty else 0.0
        )
        previous_orders = (
            int(previous["delivered_orders"].iloc[0])
            if not previous.empty else 0
        )
        current_orders = (
            int(current["delivered_orders"].iloc[0])
            if not current.empty else 0
        )

        change = current_revenue - previous_revenue

        results.append({
            "state": state,
            "previous_revenue": round(previous_revenue, 2),
            "current_revenue": round(current_revenue, 2),
            "revenue_change": round(change, 2),
            "revenue_change_pct": (
                round(change / previous_revenue * 100, 2)
                if previous_revenue else None
            ),
            "previous_delivered_orders": previous_orders,
            "current_delivered_orders": current_orders,
            "previous_average_order_value": (
                round(previous_revenue / previous_orders, 2)
                if previous_orders else None
            ),
            "current_average_order_value": (
                round(current_revenue / current_orders, 2)
                if current_orders else None
            ),
            "previous_customers": (
                int(previous["customers"].iloc[0]) if not previous.empty else 0
            ),
            "current_customers": (
                int(current["customers"].iloc[0]) if not current.empty else 0
            ),
        })

    results.sort(key=lambda row: row["revenue_change"])

    regional_change = sum(row["revenue_change"] for row in results)
    if abs(regional_change - overall_revenue_change) > 0.02:
        raise ValueError("Regional revenue changes do not reconcile.")

    return results


def _build_customer_diagnosis(
    data: pd.DataFrame,
    previous_month: str,
    current_month: str,
    overall_revenue_change: float,
) -> list[dict]:
    monthly = (
        data.groupby(["customer_unique_id", "month"])
        .agg(
            revenue=("price", "sum"),
            delivered_orders=("order_id", "nunique"),
        )
        .reset_index()
    )

    previous = (
        monthly[monthly["month"].eq(previous_month)]
        .drop(columns="month")
        .rename(columns={
            "revenue": "previous_revenue",
            "delivered_orders": "previous_delivered_orders",
        })
    )

    current = (
        monthly[monthly["month"].eq(current_month)]
        .drop(columns="month")
        .rename(columns={
            "revenue": "current_revenue",
            "delivered_orders": "current_delivered_orders",
        })
    )

    comparison = previous.merge(
        current,
        on="customer_unique_id",
        how="outer",
    ).fillna(0)

    comparison["revenue_change"] = (
        comparison["current_revenue"] - comparison["previous_revenue"]
    )

    comparison["status"] = "retained"
    comparison.loc[
        comparison["previous_delivered_orders"].eq(0), "status"
    ] = "new"
    comparison.loc[
        comparison["current_delivered_orders"].eq(0), "status"
    ] = "inactive"

    grouped = (
        comparison.groupby("status")
        .agg(
            customers=("customer_unique_id", "nunique"),
            previous_revenue=("previous_revenue", "sum"),
            current_revenue=("current_revenue", "sum"),
            previous_delivered_orders=("previous_delivered_orders", "sum"),
            current_delivered_orders=("current_delivered_orders", "sum"),
            revenue_change=("revenue_change", "sum"),
        )
    )

    descriptions = {
        "new": "Delivered-order customers active only in the current month.",
        "retained": "Customers with delivered orders in both months.",
        "inactive": (
            "Customers active in the previous month with no delivered "
            "order in the current comparison month; not proof of permanent churn."
        ),
    }

    results = []
    for status in ("new", "retained", "inactive"):
        row = grouped.loc[status] if status in grouped.index else None

        if row is None:
            customers = previous_revenue = current_revenue = 0
            previous_orders = current_orders = revenue_change = 0
        else:
            customers = int(row["customers"])
            previous_revenue = float(row["previous_revenue"])
            current_revenue = float(row["current_revenue"])
            previous_orders = int(row["previous_delivered_orders"])
            current_orders = int(row["current_delivered_orders"])
            revenue_change = float(row["revenue_change"])

        results.append({
            "status": status,
            "description": descriptions[status],
            "customers": customers,
            "previous_revenue": round(previous_revenue, 2),
            "current_revenue": round(current_revenue, 2),
            "revenue_change": round(revenue_change, 2),
            "previous_delivered_orders": previous_orders,
            "current_delivered_orders": current_orders,
            "previous_average_revenue_per_customer": (
                round(previous_revenue / customers, 2) if customers else None
            ),
            "current_average_revenue_per_customer": (
                round(current_revenue / customers, 2) if customers else None
            ),
        })

    customer_change = sum(row["revenue_change"] for row in results)
    if abs(customer_change - overall_revenue_change) > 0.02:
        raise ValueError("Customer revenue changes do not reconcile.")

    return results


def build_regional_customer_diagnosis(
    previous_month: str,
    current_month: str,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    customers: pd.DataFrame,
) -> dict:
    data = _prepare_delivered_data(
        previous_month,
        current_month,
        orders,
        items,
        customers,
    )

    overall = (
        data.groupby("month")["price"].sum().to_dict()
    )
    previous_revenue = float(overall.get(previous_month, 0.0))
    current_revenue = float(overall.get(current_month, 0.0))
    revenue_change = current_revenue - previous_revenue

    regional = _build_regional_diagnosis(
        data,
        previous_month,
        current_month,
        revenue_change,
    )
    customer_segments = _build_customer_diagnosis(
        data,
        previous_month,
        current_month,
        revenue_change,
    )

    return {
        "previous_month": previous_month,
        "current_month": current_month,
        "previous_revenue": round(previous_revenue, 2),
        "current_revenue": round(current_revenue, 2),
        "revenue_change": round(revenue_change, 2),
        "regional_drivers": regional,
        "customer_segments": customer_segments,
        "methodology": {
            "revenue_basis": "Delivered item prices, excluding freight.",
            "customer_identity": "customer_unique_id.",
            "activity_basis": "At least one delivered order in the month.",
            "inactive_customer_warning": (
                "Inactive means no delivered order in the current comparison "
                "month. It does not establish permanent churn."
            ),
        },
    }


def load_regional_customer_diagnosis(
    previous_month: str,
    current_month: str,
) -> dict:
    orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
    items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
    customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")

    return build_regional_customer_diagnosis(
        previous_month,
        current_month,
        orders,
        items,
        customers,
    )
