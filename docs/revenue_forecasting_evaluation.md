# RevenuePilot — Revenue Forecasting Evaluation

## 1. Purpose

Document the forecasting benchmarks, validation approach, measured results,
and limitations used to evaluate weekly delivered item value forecasts.

The objective is to select a defensible forecasting approach using
chronological evaluation rather than relying on a single favorable test period.

## 2. Data and metric definition

Source: weekly aggregation loaded by `src/evaluate_revenue_forecast.py`
from the PostgreSQL `orders` table.

Forecast target: weekly sum of `item_value` for orders whose status is
`delivered`.

The target is delivered item value, not profit, cash flow, or audited
accounting revenue.

The available weekly series contains 86 observations from 2017-01-02
through 2018-08-20.

## 3. Evaluation metrics

- MAE: mean absolute error, expressed in Brazilian reais (R$).
- RMSE: root mean squared error, which gives greater weight to large errors.
- WAPE: sum of absolute errors divided by the sum of actual values,
  expressed as a percentage.

Lower values indicate better performance for each metric.

## 4. Initial chronological holdout

The initial evaluation reserves the final 12 weeks for testing.

- Training period: 2017-01-02 through 2018-05-28.
- Test period: 2018-06-04 through 2018-08-20.
- Training observations: 74 weeks.
- Test observations: 12 weeks.

Results from the chronological 12-week holdout:

| Model | MAE (R$) | RMSE (R$) | WAPE |
|---|---:|---:|---:|
| Damped trend (factor 0.25) | 51,858.52 | 63,895.74 | 25.23% |
| Linear trend | 59,917.19 | 74,189.41 | 29.15% |
| Mean baseline | 64,092.82 | 75,416.88 | 31.18% |
| Seasonal naive | 97,816.11 | 105,462.43 | 47.59% |

On this holdout, damped trend reduces WAPE by 13.44% relative to linear
trend and by 19.09% relative to the mean baseline. These are relative
reductions in WAPE, not percentage-point differences. The seasonal-naive
benchmark performs worse.

An exploratory comparison on this same holdout tested constant forecasts
based on the mean of the final 4, 8, and 13 training weeks:

| Model | MAE (R$) | RMSE (R$) | WAPE |
|---|---:|---:|---:|
| 4-week average | 37,447.95 | 45,420.54 | 18.22% |
| 8-week average | 39,128.14 | 47,894.46 | 19.04% |
| 13-week average | 38,123.23 | 46,863.99 | 18.55% |

These rolling-average benchmarks use one mean calculated from the training
period and repeat it across all 12 test weeks. They do not update the mean
during the test period.

The rolling-average results are exploratory comparisons and are not yet
integrated into the production forecasting implementation.

## 5. Expanding-window backtest

A second experiment evaluates eight chronological folds. Each fold uses
all observations available before its test period and forecasts the next
four weeks. The first training window contains 52 weeks; subsequent
training windows expand. Predictions are evaluated over 32 test weeks
in total.

Aggregate results across the same 32 evaluated weeks:

| Model | MAE (R$) | RMSE (R$) | WAPE |
|---|---:|---:|---:|
| Damped trend (factor 0.25) | 30,983.58 | 43,510.55 | 14.50% |
| Linear trend | 32,730.49 | 45,593.26 | 15.32% |
| 13-week average | 33,552.73 | 41,324.85 | 15.70% |
| 8-week average | 34,448.33 | 43,851.49 | 16.12% |
| 4-week average | 37,891.76 | 49,408.49 | 17.73% |
| Mean baseline | 80,526.06 | 87,587.08 | 37.68% |
| Seasonal naive | 130,451.92 | 137,461.73 | 61.04% |

Damped trend has the lowest aggregate WAPE among these candidates in this
backtest. The 13-week average has lower RMSE, so the model choice depends
partly on which error characteristic matters most. The four-week average,
despite its strong initial holdout result, does not lead in this
expanding-window comparison.

Fold-level results qualify the aggregate improvement: damped trend still
has high WAPE in folds 6 and 7 (37.86% and 47.16%). The 13-week average
performs better on those folds. The damped model is therefore a promising
candidate, not a universally superior model.

The metrics from the initial 12-week holdout and the 32-week backtest
must not be compared as if they came from the same test observations.

## 6. Trend-window experiments

Additional exploratory experiments fitted linear trends to the most recent
13, 26, or 39 training weeks at each fold.

| Model | MAE (R$) | RMSE (R$) | WAPE |
|---|---:|---:|---:|
| Full-history trend | 32,730.49 | 45,593.26 | 15.32% |
| 39-week trend | 33,753.00 | 44,123.98 | 15.79% |
| 26-week trend | 34,002.68 | 43,848.07 | 15.91% |
| 13-week trend | 40,606.80 | 55,240.85 | 19.00% |

The full-history trend has the lowest aggregate WAPE among these candidates.
The 26-week trend wins more individual folds in the tested comparison, but
its aggregate WAPE is slightly higher. Fold win counts alone are not a
sufficient selection criterion.

## 7. Diagnostic observations

Weekly revenue diagnostics found:

- 86 weekly observations and no zero-revenue weeks.
- Mean weekly delivered item value: R$153,144.90.
- Median weekly delivered item value: R$141,551.58.
- Standard deviation: R$71,823.10.
- Minimum: R$3,114.96.
- Maximum: R$397,906.24.
- Lag-1 autocorrelation: 0.821.
- Lag-13 autocorrelation: 0.658.
- Lag-52 autocorrelation: 0.093.

Large week-over-week changes and periods of declining revenue contribute to
forecast errors. In some folds, the linear trend continues predicting
increasing revenue while actual revenue declines.

The low lag-52 autocorrelation and weak seasonal-naive results do not
establish a reliable annual seasonal pattern. The available series is also
too short to make strong claims about recurring annual effects.

## 8. Adaptive model-selection experiment

Two selectors were evaluated against the fixed linear-trend and 13-week
average models using the same eight-fold, four-week expanding-window
backtest.

- Full-history selector: selects between the linear trend and 13-week
  average using all eligible inner validation windows within each outer
  training window.
- Recent-window selector: makes the same choice using only the two most
  recent eligible inner validation windows.

The outer test periods remain chronological and separate from the inner
validation windows used to make each selection.

Aggregate results across the same 32 outer test weeks:

| Model | MAE (R$) | RMSE (R$) | WAPE |
|---|---:|---:|---:|
| Linear trend | 32,730.49 | 45,593.26 | 15.32% |
| Full-history selector | 32,730.49 | 45,593.26 | 15.32% |
| 13-week average | 33,552.73 | 41,324.85 | 15.70% |
| Recent-window selector | 38,362.67 | 49,704.88 | 17.95% |

The full-history selector chose the linear trend in all eight outer folds
and therefore produced the same predictions as the fixed trend model.
The recent-window selector chose the 13-week average in two folds and the
linear trend in six folds. Its aggregate WAPE was 2.63 percentage points
higher than the fixed linear trend.

The experiment does not demonstrate a benefit from adaptive model
selection. The recent-window selector was less accurate in aggregate, while
the full-history selector added complexity without changing the selected
model.

## 9. Current model-selection decision

Use damped linear trend with damping factor 0.25 as the current historical
demo forecast model. It achieved 25.23% WAPE on the chronological 12-week
holdout and 14.50% WAPE across the eight-fold, four-week expanding-window
backtest. It outperformed the undamped linear trend on aggregate WAPE in
both evaluations.

This choice is provisional. Damped trend still performs poorly in backtest
folds 6 and 7, where the 13-week average has lower WAPE. The 13-week
average also has lower aggregate RMSE across the eight folds. The adaptive
selector experiments do not demonstrate a benefit from adding model
selection complexity.

These results support a historical demonstration model, not a claim that
the forecast is production-ready or will always perform best. Continue to
report the evaluation period, forecast horizon, target definition, and
model limitations alongside forecast results.

## 10. Limitations

- The dataset is historical and ends on 2018-10-17 at the source level.
  These forecasts are historical demonstrations, not current revenue
  predictions.
- The weekly series contains only 86 observations.
- The evaluation does not establish causation for revenue changes.
- No prediction intervals or calibrated uncertainty estimates are included.
- The tested models do not incorporate external drivers, promotions,
  product mix, or explicit change-point detection.
- Results can vary across test periods and forecast horizons.
- The current backtest uses overlapping training histories and evaluates
  a limited number of historical periods.

## 11. Reproducibility

Current evaluation entry point:

`src/evaluate_revenue_forecast.py`

Run the existing holdout evaluation with:

`.venv/bin/python -m src.evaluate_revenue_forecast`

The expanding-window backtest is available through the evaluation
runner. The alternate trend-window and adaptive model-selection experiments
were run as exploratory terminal scripts and are not yet implemented as
permanent automated evaluation routines.
