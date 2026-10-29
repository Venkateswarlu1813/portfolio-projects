# RFM Customer Segmentation

Turn fictional transaction history into interpretable customer groups.

## Method
Generate transactions for 300 synthetic customers. Each row is one order with a positive amount. At a fixed snapshot (`2026-01-01`), aggregate recency (days since latest order), frequency (order count), and monetary value (total spend). Reject transactions on or after the snapshot. Log-transform and standardize RFM; fit KMeans for k=2..6; select the highest silhouette score. Compare the chosen partition across random seeds with adjusted Rand index. Export profiles in original units.

This is descriptive unsupervised analysis: there are no churn labels or predictive accuracy claims. Customers are generated from three spending regimes. Silhouette and seed stability cannot show that a segment is commercially useful. Profiles should be reviewed before naming segments or planning interventions. Returns, refunds, currencies, and multiple line items per order are not modelled.

## Run
`python -m portfolio customer-segmentation`

Optional: `python -m portfolio customer-segmentation --csv orders.csv --snapshot 2026-01-01` with `customer_id,date,amount`. Require at least 20 customers, 7 distinct RFM profiles, and complete positive finite amounts. Each row must represent an order; aggregate line items first.

## Outputs and next steps
`reports/segments/metrics.json` and `results.csv` with customer-to-segment assignments. Segment numbers are arbitrary. Extend with bootstrap stability, a business-reviewed naming step, cohort comparisons, and a documented approach for assigning future customers.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
