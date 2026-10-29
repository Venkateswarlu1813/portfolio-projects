# Stockroom — Inventory Operations

Track products and stock movements while preserving a consistent balance and audit ledger.

## Run and walkthrough
`python -m portfolio inventory --port 5001`

Open http://127.0.0.1:5001. Register a local account. Add **Notebook / NOTE-01** with reorder level 5. Open **Record stock movement**, receive +10 with reason **Opening delivery**, then issue -3 with reason **Customer order**. The balance is 7. Try -20: the request is rejected, the balance remains 7, and no ledger row is recorded. Issue -3 again to trigger the reorder alert. View history, filter products, and export CSV.

## Implementation
Flask + server-rendered frontend + a dedicated SQLite database. Products are unique by SKU within a workspace. Stock updates use an atomic guarded SQL update and record the ledger entry in the same transaction. Negative balances and zero movements are rejected. Discontinued products must be reactivated before a movement can be recorded. Receipts/issues are integer units only.

## Scope
Local demonstration. No money handling, order processing, unit conversion, arbitrary edits/deletion, procurement, or external integrations. Accounts have separate workspaces; this project does not expose shared staff roles. Extend with supplier purchase orders, stock counts, multi-location transfers, transaction idempotency keys, and batch/serial tracking.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
