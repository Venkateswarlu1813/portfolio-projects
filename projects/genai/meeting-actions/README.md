# Minute — Evidence-backed Meeting Actions

Extract owner, task, due date, and verbatim evidence from supplied meeting notes.

## Workflow
Offline mode is an explicit parser for `ACTION: owner | task | due` lines. It deliberately ignores general conversation and suggestions. OpenAI mode accepts ordinary transcripts and requests a strict summary/actions schema. Every action needs a nonempty exact evidence substring present in the transcript; otherwise reject the entire output. Missing owners/dates are requested as `unspecified`; relative dates stay as written. The program does not invent a calendar reference date or send invitations.

## Run
`python -m portfolio meeting-actions --port 5102`

Open http://127.0.0.1:5102. The bundled transcript includes two explicit action records and an uncommitted mobile-dashboard suggestion. Offline output contains only the two records. CLI: `python -m portfolio meeting-actions --text "ACTION: Dev | Write tests | Friday"`.

## Generation and limitations
Optional OpenAI mode requires local credentials and consent; see the root guide. Exact quote checks catch fabricated evidence, but cannot verify that every owner/task/date is correctly inferred from the quote. Short quotes may be ambiguous. A human should review extracted actions before creating tasks. Extend with speaker IDs, a timestamped transcript model, date resolution with an explicit meeting date/timezone, and labelled evaluation for suggestion-versus-commitment errors.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
