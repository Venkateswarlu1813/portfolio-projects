# Daily Demand Forecasting

Predict tomorrow's demand from prior observations, with an explicit time-based evaluation protocol.

## Method
Generate 560 synthetic daily observations with weekly seasonality, a trend, and noise. Features are lags 1, 7, 14, 28, a shifted seven-day rolling mean, and weekday sine/cosine. Reserve the last 56 days as holdout. Select Ridge regularization using four expanding-window splits within training. Compare MAE/RMSE with a seven-day seasonal-naive baseline.

This is **rolling one-day-ahead evaluation**: after each day is observed, its true value is available for the next prediction. Validation uses the same protocol. It is not a fixed-origin 56-day future forecast. Rolling statistics are shifted before fitting. Dates are sorted and validated as consecutive daily observations.

## Run
`python -m portfolio demand-forecasting`

Optional: `python -m portfolio demand-forecasting --csv demand.csv` with `date,demand`, ISO dates, at least 140 days, and finite nonnegative demand. Duplicated dates, gaps, and missing targets are rejected.

## Outputs and next steps
`reports/demand/metrics.json` and `results.csv`, including actuals, model predictions, and seasonal baseline. Extend with probabilistic intervals, holiday covariates known in advance, drift monitoring, and a recursive multi-step evaluation. Synthetic results do not establish commercial forecasting accuracy.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
