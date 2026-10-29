# Customer Churn Prediction

Estimate a synthetic customer's churn probability and compare a learned classifier with a prior-only baseline.

## Method
Generate 2,000 fictional customers (seed 42). Churn is sampled from a noisy logistic probability depending on tenure, charges, support tickets, and contract type. A few charges are missing. Split 60/20/20 into stratified training, validation, and untouched test sets. Fit imputation, scaling, and categorical encoding only on the training split. Train logistic regression; select the F1 threshold on validation; report ROC-AUC, average precision, F1, confusion matrix, and held-out permutation importance.

The target is generated from these features, so strong test results only demonstrate implementation. They are not evidence of useful performance on real telecom customers. Permutation importance describes model dependence, not causation. A real dataset needs a time-defined churn window, temporal or grouped validation, calibration, fairness review, and cost-based threshold selection.

## Run
`python -m portfolio churn-prediction`

Optional: `python -m portfolio churn-prediction --csv customers.csv` with columns `tenure,monthly_charge,support_tickets,contract,churn`. Target must be complete binary 0/1. At least 100 rows are required; sufficient examples per class are needed for stratification. All other columns are ignored. The demo omits customer identifiers; do not split repeated real customers across partitions.

## Outputs and next steps
`reports/churn/metrics.json` and `results.csv`. Review false positives/negatives and compare average precision with the baseline. Extend with calibration plots, a customer-level temporal split, an inference artifact, and measured intervention costs.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
