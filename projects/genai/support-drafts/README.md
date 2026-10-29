# ReplyDesk — Policy-grounded Support Drafts

Draft a customer support response from a versioned fictional policy document, leaving account decisions to a human.

## Workflow
Retrieve relevant paragraphs from `portfolio/data/policies` using TF-IDF/cosine similarity. Offline mode renders a courteous template plus exact policy excerpts. OpenAI mode generates a structured draft, citation IDs, and a human-review flag. Unknown citation IDs are rejected. A request without matching sources is escalated without a provider call. Nothing sends a message, approves a refund, changes an account, or accesses billing systems.

## Run
`python -m portfolio support-drafts --port 5101`

Open http://127.0.0.1:5101. Try **Can I get a refund?** and inspect the fictional 14-day review policy. Try **I cannot sign in** and inspect the reset policy. CLI: `python -m portfolio support-drafts --text "Can I get a refund?"`.

## Generation and limitations
OpenAI mode requires your own local API configuration and explicit UI consent; see the root guide. Every generated response is a draft for human review, regardless of the model flag. Retrieval scores are not probabilities. Existing citation IDs do not prove every sentence is supported. Real deployment needs approved policies, access control, version ownership, grounded-answer evaluation, PII handling, and mandatory review before sending. These policies are invented solely for the demonstration.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
