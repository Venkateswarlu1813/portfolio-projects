# CareerBoard — Job Application Tracker

A complete local browser-to-database workflow for managing applications and follow-ups.

## Run and walkthrough
`python -m portfolio job-tracker --port 5000`

Open http://127.0.0.1:5000. Register a local account, add **Fictional Labs / Python Developer**, set a follow-up date, and save. Move it Saved → Applied → Interview → Offer. Attempt Saved → Offer to see validation. Rejected applications may be reopened to Saved. Open **View history** to inspect the changes. Search by company/role, filter status, export CSV, sign out, and sign in to confirm persistence.

## Implementation
Server-rendered HTML forms, Flask routes, and a dedicated SQLite database. Bound SQL, password hashing, CSRF form tokens, workspace membership checks, and audit history. Dashboard counts and due follow-ups are computed from stored records. Duplicate role text in a workspace is rejected by the shared schema; use a distinct role or requisition identifier when tracking similar roles at different companies.

## Scope
Local demonstration, not a recruitment platform. No email scraping, job recommendations, auto-applying, arbitrary edits, deletion, or reminders. Dates are user-entered and due counters use the server's date. See root deployment notes before any public hosting. Extend with company+requisition uniqueness, interview events, reminders, and application document attachments.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
