# Venkateswarlu's Project Lab

**Three data science projects. Three GenAI workflows. Three full-stack applications.**

Nine runnable portfolio demonstrations, built in Python with reproducible examples and automated checks. Each project has its own entry point and guide. Shared modules make authentication, retrieval, and model evaluation easier to inspect and maintain.

These are local portfolio demonstrations, not production deployments. The data science datasets and AI policy documents are deliberately synthetic. No claimed business outcomes, real customer data, or invented model accuracy.

## Explore the nine projects

| Track | Project | What you can inspect |
| --- | --- | --- |
| Data science | [Churn prediction](projects/data-science/churn-prediction) | Train/validation/test split, logistic model, threshold tuning, baseline and permutation importance |
| Data science | [Demand forecasting](projects/data-science/demand-forecasting) | Lag features, expanding-window validation, seasonal baseline, one-day-ahead holdout |
| Data science | [Customer segmentation](projects/data-science/customer-segmentation) | Transaction-to-RFM pipeline, log scaling, silhouette model selection, stability |
| GenAI | [Document Q&A](projects/genai/document-qa) | TF-IDF retrieval, source IDs, evidence-limited generation, abstention |
| GenAI | [Support drafts](projects/genai/support-drafts) | Policy retrieval, human review, cited drafts, no external actions |
| GenAI | [Meeting actions](projects/genai/meeting-actions) | Structured action extraction, quote validation, conservative offline parser |
| Full stack | [CareerBoard](projects/full-stack/job-tracker) | Sign-in, application stages, follow-ups, history, CSV export |
| Full stack | [Stockroom](projects/full-stack/inventory) | Stock receipts/issues, atomic balance checks, ledger, reorder alerts |
| Full stack | [TeamFlow](projects/full-stack/team-tasks) | Workspace membership, assignment, task states, shared history |

## Quick start

Requires **Python 3.11+**. Run these commands from this repository's root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m portfolio job-tracker --port 5000
```

On macOS/Linux use `.venv/bin/python` in place of `.venv\Scripts\python`. Open [localhost:5000](http://127.0.0.1:5000), choose **Create an account**, then create a username and a password of at least 12 characters. There are no hardcoded credentials.

To run another app, replace `job-tracker` with `inventory`, `team-tasks`, `document-qa`, `support-drafts`, or `meeting-actions`. Use a different `--port` when running multiple apps. Each full-stack project has a separate SQLite database created on first run.

```powershell
# Generate measured data science reports without downloading any data
.venv\Scripts\python -m portfolio churn-prediction
.venv\Scripts\python -m portfolio demand-forecasting
.venv\Scripts\python -m portfolio customer-segmentation

# Run an offline AI workflow once without starting a browser
.venv\Scripts\python -m portfolio document-qa --text "How long are backups retained?"

# Verify all projects; no API key or network needed after dependency installation
.venv\Scripts\python -m pytest -q
```

Data science outputs are written to `reports/<project>/metrics.json` and `results.csv`. Checked example results and data provenance are in [examples](examples). The nine folder-level `run.py` entry points also work after installing the root package.

## Optional OpenAI generation

Offline mode makes **no model calls**: Q&A returns excerpts, support returns a review template with excerpts, and meeting extraction only parses explicit `ACTION: owner | task | due` records. It is labelled offline throughout the UI.

For generated responses, set these environment variables **locally**, using your own API account. Do not paste keys into chat or commit them:

```powershell
$env:OPENAI_API_KEY = "your-key-in-your-local-shell"
$env:OPENAI_MODEL = "a-supported-model-available-to-your-account"
.venv\Scripts\python -m portfolio document-qa --port 5100
```

Choose OpenAI mode and confirm sending the text and retrieved context. Requests use the [Responses API with strict structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), a 45-second timeout, a bounded output, and `store=false`. No automatic retries or silent fallback. API calls may incur charges. `store=false` does not mean zero provider retention; review your provider's data policies.

Tests cover the request/response contract using a fake transport. **Live model calls have not been verified with a real API key.** Schema and citation validation do not prove semantic correctness; human review remains required. Source text is treated as untrusted context, but prompt-based defenses cannot guarantee resistance to every injection.

## Architecture and code map

- `portfolio/data_science.py`: three independent experiment pipelines.
- `portfolio/genai.py`: three AI workflows, retrieval, schemas, provider adapter.
- `portfolio/ai_web.py`: browser forms for the AI workflows.
- `portfolio/web.py`: full-stack domain routes, membership checks, persistence, and sessions.
- `portfolio/templates` and `portfolio/static`: responsive, server-rendered interfaces; no frontend build required.
- `projects`: nine entry points, walkthroughs, methods, limitations, and extension ideas.
- `tests`: data validation, end-to-end server flows, isolation, transaction rollback, provider contract, evidence validation.

The web apps use HTML forms → Flask routes → SQLite transactions → rendered responses. Passwords are hashed with Werkzeug; writes require CSRF tokens; queries use bound parameters; templates escape text; CSV exports neutralize formula prefixes. TeamFlow's owner can add registered teammates to the current workspace. Members can update tasks; only the owner can add members.

## Scope and limitations

Local servers bind to `127.0.0.1` and run with debug disabled. Flask's development server is for local review. Before public deployment, add HTTPS, secure cookies, a stable secret, production hosting, monitoring, backups, migration tooling, account recovery, and stronger abuse controls. The current database-backed login limiter is per username and intended for demonstration.

Full-stack apps support creation, status updates, search/filtering, history, and export. They do not implement arbitrary record editing/deletion, email invitations, payments, password reset, or enterprise roles. SQLite suits the local demo; a shared production service needs a deployment-specific persistence strategy. Shared source code is intentional, and the nine projects live in this single repository.

## Validation

Run `python -m pytest -q`. CI repeats tests and executes all three data pipelines on Python 3.11. See [VALIDATION.md](VALIDATION.md) for measured results and current verification limits.

Built for [Venkateswarlu Vennampalli](https://github.com/Venkateswarlu1813).
