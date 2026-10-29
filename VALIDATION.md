# Validation record

Date: 29 October 2026. Local environment: Windows, Python 3.11.

## Automated checks

`python -m pytest -q`: **35 passed**.

- Three data science pipelines: validation splits, baseline comparisons, complete outputs, daily continuity, snapshot boundaries, nonempty and stable segments.
- Three AI workflows: traceable excerpts, unknown-query abstention, human-review drafts, explicit action parsing, missing credentials, invented evidence/citation rejection, and strict provider response parsing.
- Provider contract uses a **fake HTTP transport**: validates request shape, no storage flag, incomplete output, refusal, and malformed schema handling. No real API key or live model output was used.
- Full-stack flow tests: registration, sign-in, record persistence, hashed passwords, workspace isolation, unauthorized access rejection, CSRF, escaped HTML, formula-safe CSV, rate limiting, atomic stock/ledger consistency, job-stage transitions, membership, assignment, and distinct session-cookie names.

## Browser → server → data → rendered response

All six browser interfaces loaded from local running servers.

| Project | Observed browser flow |
| --- | --- |
| Stockroom | Register → add product → receive 24 units → rendered balance 24 and low-stock count 0 |
| CareerBoard | Register → add Fictional Labs / Python Developer → move Saved to Applied → history shows actor and transition |
| TeamFlow | Register → create a task with due date → assign it to current member → rendered task and assignee |
| Atlas | Submit backup-retention question → 30-day paragraph with handbook source ID |
| ReplyDesk | Submit refund request → fictional 14-day policy excerpt and human-review draft |
| Minute | Submit bundled transcript → two action records and their exact quotes |

The automated tests additionally exercise multi-user membership and denial cases. Browser review was at a desktop viewport; mobile CSS is included but a full mobile accessibility audit has not been completed. A session-cookie collision found during multi-app review was fixed and covered by a regression check.

## Installation and experiment runs

- Editable install with development dependencies completed successfully.
- All three data science CLI commands ran successfully and produced the checked `examples/*` files.
- UI templates and project package data loaded successfully from the installed package.

## Practical limits

Not verified: real OpenAI generation quality, production hosting, public deployment, large datasets, high concurrency, or real customer/model performance. These are functional local portfolio demonstrations with shared infrastructure. None is represented as a deployed production service.

CI is configured to repeat the tests and all data experiments on GitHub. Local results above do not imply that a remote CI run has completed; inspect the Actions tab for its latest status.
