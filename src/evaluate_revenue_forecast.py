import json

import pandas as pd

from backend.database import get_connection
from src.revenue_forecasting import (
    evaluate_expanding_window,
    evaluate_linear_trend,
)


def load_weekly_revenue() -> pd.DataFrame:
    query = """
        SELECT
            DATE_TRUNC('week', order_purchase_timestamp)::date AS week_start,
            COALESCE(
                SUM(item_value) FILTER (
                    WHERE order_status = 'delivered'
                ),
                0
            ) AS delivered_revenue
        FROM orders
        WHERE order_purchase_timestamp >= DATE '2017-01-01'
          AND order_purchase_timestamp < DATE '2018-09-01'
        GROUP BY 1
        HAVING DATE_TRUNC('week', order_purchase_timestamp)::date
               + 7 <= DATE '2018-09-01'
        ORDER BY week_start;
    """

    with get_connection() as conn:
        rows = conn.execute(query).fetchall()

    return pd.DataFrame(
        [dict(row) for row in rows],
        columns=["week_start", "delivered_revenue"],
    )


def main() -> None:
    weekly_data = load_weekly_revenue()
    results = evaluate_linear_trend(weekly_data, test_weeks=12)
    backtest = evaluate_expanding_window(
        weekly_data,
        horizon=4,
        initial_train_weeks=52,
        step_size=4,
    )

    print("RevenuePilot | Weekly Revenue Forecast Evaluation")
    print("=" * 52)
    print(f"Weekly observations: {len(weekly_data)}")
    print(f"Training period: {results['training_start']} to {results['training_end']}")
    print(f"Test period:     {results['test_start']} to {results['test_end']}")
    print(f"Training weeks:  {results['training_weeks']}")
    print(f"Test weeks:      {results['test_weeks']}")
    print()

    model_names = ["baseline", "linear_trend"]
    if "seasonal_naive" in results:
        model_names.append("seasonal_naive")

    for model_name in model_names:
        metrics = results[model_name]
        print(model_name.replace("_", " ").title())
        print(f"  MAE:     R${metrics['mae']:,.2f}")
        print(f"  RMSE:    R${metrics['rmse']:,.2f}")
        print(f"  WAPE:    {metrics['wape_pct']:.2f}%")
        print()

    baseline_wape = results["baseline"]["wape_pct"]
    trend_wape = results["linear_trend"]["wape_pct"]

    if trend_wape < baseline_wape:
        improvement = (baseline_wape - trend_wape) / baseline_wape * 100
        print(f"Trend model WAPE improvement: {improvement:.2f}%")
    else:
        print("The trend model did not beat the average baseline on WAPE.")

    print("\nStructured holdout results:")
    print(json.dumps(results, indent=2))

    print("\nExpanding-window backtest")
    print("=" * 52)
    print(f"Folds:            {backtest['fold_count']}")
    print(f"Evaluated weeks:  {backtest['evaluated_weeks']}")
    print(f"Forecast horizon: {backtest['horizon']} weeks")
    print("\nAggregate metrics across all evaluated weeks:")
    for model_name, metrics in backtest["aggregate_metrics"].items():
        print(model_name.replace("_", " ").title())
        print(f"  MAE:  R${metrics['mae']:,.2f}")
        print(f"  RMSE: R${metrics['rmse']:,.2f}")
        print(f"  WAPE: {metrics['wape_pct']:.2f}%")
    print("\nStructured backtest results:")
    print(json.dumps(backtest, indent=2))


if __name__ == "__main__":
    main()
