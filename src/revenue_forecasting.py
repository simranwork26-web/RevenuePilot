from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"week_start", "delivered_revenue"}


def prepare_weekly_revenue(data: pd.DataFrame) -> pd.DataFrame:
    """Validate and prepare a continuous weekly revenue series."""
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    result = data[["week_start", "delivered_revenue"]].copy()
    result["week_start"] = pd.to_datetime(
        result["week_start"], errors="raise"
    )
    result["delivered_revenue"] = pd.to_numeric(
        result["delivered_revenue"], errors="raise"
    )

    if result["week_start"].isna().any():
        raise ValueError("week_start cannot contain missing values")
    if result["delivered_revenue"].isna().any():
        raise ValueError("delivered_revenue cannot contain missing values")
    if not np.isfinite(result["delivered_revenue"]).all():
        raise ValueError("delivered_revenue must contain finite values")
    if (result["delivered_revenue"] < 0).any():
        raise ValueError("delivered_revenue cannot be negative")

    result = result.sort_values("week_start").reset_index(drop=True)

    if result["week_start"].duplicated().any():
        raise ValueError("week_start must be unique")
    if not result["week_start"].diff().dropna().eq(
        pd.Timedelta(days=7)
    ).all():
        raise ValueError("Observations must be exactly seven days apart")
    if len(result) < 3:
        raise ValueError("At least three weekly observations are required")

    return result


def forecast_linear_trend(
    training: pd.DataFrame,
    horizon: int = 4,
) -> pd.DataFrame:
    """Fit a linear trend to training revenue and forecast future weeks."""
    history = prepare_weekly_revenue(training)

    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer")

    x = np.arange(len(history), dtype=float)
    y = history["delivered_revenue"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, deg=1)

    future_x = np.arange(
        len(history), len(history) + horizon, dtype=float
    )
    predictions = np.maximum(intercept + slope * future_x, 0.0)
    future_dates = pd.date_range(
        start=history["week_start"].iloc[-1] + pd.Timedelta(days=7),
        periods=horizon,
        freq="7D",
    )

    return pd.DataFrame({
        "week_start": future_dates,
        "forecast_revenue": predictions,
    })


def forecast_seasonal_naive(
    training: pd.DataFrame,
    horizon: int = 4,
    season_length: int = 52,
) -> pd.DataFrame:
    """Forecast each future week using revenue from the prior seasonal cycle."""
    history = prepare_weekly_revenue(training)

    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if not isinstance(season_length, int) or isinstance(season_length, bool):
        raise ValueError("season_length must be a positive integer")
    if season_length < 1:
        raise ValueError("season_length must be a positive integer")
    if len(history) < season_length:
        raise ValueError(
            f"At least {season_length} observations are required"
        )
    if horizon > season_length:
        raise ValueError("horizon cannot exceed season_length")

    predictions = history["delivered_revenue"].iloc[
        -season_length:-season_length + horizon
    ].to_numpy(dtype=float)

    future_dates = pd.date_range(
        start=history["week_start"].iloc[-1] + pd.Timedelta(days=7),
        periods=horizon,
        freq="7D",
    )

    return pd.DataFrame({
        "week_start": future_dates,
        "forecast_revenue": predictions,
    })


def evaluate_forecast(
    actual: pd.Series,
    predicted: pd.Series,
) -> dict[str, float]:
    """Calculate MAE, RMSE, and WAPE for aligned values."""
    actual_values = np.asarray(actual, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)

    if actual_values.ndim != 1 or predicted_values.ndim != 1:
        raise ValueError("Actual and predicted values must be one-dimensional")
    if len(actual_values) == 0 or len(actual_values) != len(predicted_values):
        raise ValueError("Actual and predicted values must have equal nonzero lengths")
    if not np.isfinite(actual_values).all() or not np.isfinite(predicted_values).all():
        raise ValueError("Actual and predicted values must be finite")
    if (actual_values < 0).any() or (predicted_values < 0).any():
        raise ValueError("Revenue values cannot be negative")

    errors = actual_values - predicted_values
    absolute_errors = np.abs(errors)
    total_actual = actual_values.sum()
    wape = (
        float(100 * absolute_errors.sum() / total_actual)
        if total_actual > 0
        else float("nan")
    )

    return {
        "mae": float(absolute_errors.mean()),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "wape_pct": wape,
    }


def evaluate_linear_trend(
    weekly_data: pd.DataFrame,
    test_weeks: int = 12,
) -> dict:
    """Compare linear trend and average baselines on a chronological holdout."""
    data = prepare_weekly_revenue(weekly_data)

    if not isinstance(test_weeks, int) or isinstance(test_weeks, bool):
        raise ValueError("test_weeks must be an integer")
    if test_weeks < 1 or test_weeks >= len(data) - 2:
        raise ValueError(
            "test_weeks must leave at least three training observations"
        )

    training = data.iloc[:-test_weeks].copy()
    test = data.iloc[-test_weeks:].copy()

    trend_predictions = forecast_linear_trend(training, horizon=test_weeks)
    baseline_predictions = np.full(
        test_weeks, training["delivered_revenue"].mean(), dtype=float
    )
    actual = test["delivered_revenue"].reset_index(drop=True)

    results = {
        "training_weeks": len(training),
        "test_weeks": len(test),
        "training_start": training["week_start"].iloc[0].date().isoformat(),
        "training_end": training["week_start"].iloc[-1].date().isoformat(),
        "test_start": test["week_start"].iloc[0].date().isoformat(),
        "test_end": test["week_start"].iloc[-1].date().isoformat(),
        "baseline": evaluate_forecast(
            actual, pd.Series(baseline_predictions)
        ),
        "linear_trend": evaluate_forecast(
            actual, trend_predictions["forecast_revenue"]
        ),
    }

    if len(training) >= 52 and test_weeks <= 52:
        seasonal_predictions = training["delivered_revenue"].iloc[
            -52:-52 + test_weeks
        ].reset_index(drop=True)
        results["seasonal_naive"] = evaluate_forecast(
            actual, seasonal_predictions
        )

    return results


def evaluate_expanding_window(
    weekly_data: pd.DataFrame,
    horizon: int = 4,
    initial_train_weeks: int = 52,
    step_size: int = 4,
) -> dict:
    """Evaluate forecasting benchmarks with expanding-window backtesting."""
    data = prepare_weekly_revenue(weekly_data)

    for name, value in (
        ("horizon", horizon),
        ("initial_train_weeks", initial_train_weeks),
        ("step_size", step_size),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    if initial_train_weeks < 3:
        raise ValueError("initial_train_weeks must be at least three")
    if len(data) < initial_train_weeks + horizon:
        raise ValueError(
            "Insufficient observations for the initial training window "
            "and one test window"
        )

    average_windows = [
        window for window in (4, 8, 13)
        if initial_train_weeks >= window
    ]
    include_seasonal = initial_train_weeks >= 52 and horizon <= 52

    fold_results = []
    all_actual = []
    all_predictions = {}

    for test_start in range(
        initial_train_weeks,
        len(data) - horizon + 1,
        step_size,
    ):
        training = data.iloc[:test_start].copy()
        test = data.iloc[test_start:test_start + horizon].copy()
        actual = test["delivered_revenue"].to_numpy(dtype=float)

        predictions = {
            "linear_trend": forecast_linear_trend(
                training, horizon=horizon
            )["forecast_revenue"].to_numpy(dtype=float),
            "baseline": np.full(
                horizon,
                training["delivered_revenue"].mean(),
                dtype=float,
            ),
        }

        for window in average_windows:
            predictions[f"{window}_week_average"] = np.full(
                horizon,
                training["delivered_revenue"].tail(window).mean(),
                dtype=float,
            )

        if include_seasonal:
            predictions["seasonal_naive"] = forecast_seasonal_naive(
                training, horizon=horizon
            )["forecast_revenue"].to_numpy(dtype=float)

        fold_results.append({
            "training_weeks": len(training),
            "test_start": test["week_start"].iloc[0].date().isoformat(),
            "test_end": test["week_start"].iloc[-1].date().isoformat(),
            "models": {
                name: evaluate_forecast(
                    pd.Series(actual), pd.Series(predicted)
                )
                for name, predicted in predictions.items()
            },
        })

        all_actual.extend(actual.tolist())
        for name, predicted in predictions.items():
            all_predictions.setdefault(name, []).extend(predicted.tolist())

    actual_series = pd.Series(all_actual)
    aggregate_metrics = {
        name: evaluate_forecast(actual_series, pd.Series(predicted))
        for name, predicted in all_predictions.items()
    }

    return {
        "horizon": horizon,
        "initial_train_weeks": initial_train_weeks,
        "step_size": step_size,
        "fold_count": len(fold_results),
        "evaluated_weeks": len(all_actual),
        "folds": fold_results,
        "aggregate_metrics": aggregate_metrics,
    }
