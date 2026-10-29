# Atlas — Document Q&A

Answer questions from a small, fictional workspace handbook and expose the retrieved evidence.

## Workflow
Read Markdown paragraphs from `portfolio/data/knowledge`. Split long paragraphs into overlapping character windows with filename/paragraph/window IDs. Rank using TF-IDF bigrams and cosine similarity, retain the top three above the 0.08 demo threshold, and pass only those sources to the optional generator. Below the retrieval threshold, abstain without calling a model. Reject unknown citation IDs and uncited non-abstained output.

## Run
`python -m portfolio document-qa --port 5100`

Open http://127.0.0.1:5100. Ask **How long are backups retained?** The offline answer shows the 30-day policy paragraph and a traceable source ID. Ask **quasar mitochondria photosynthesis** to exercise abstention. CLI: `python -m portfolio document-qa --text "How long are backups retained?"`.

## Generation and limitations
See the root guide for local `OPENAI_API_KEY` and `OPENAI_MODEL` configuration. Offline mode returns excerpts, not generated prose. OpenAI mode uses a strict answer/citations/abstained schema. Citations are checked for existence, not semantic entailment. TF-IDF can miss paraphrases or retrieve lexically related but insufficient evidence. The threshold is a demo heuristic, not calibrated confidence. Replace retrieval with embeddings, add chunk-level provenance and evaluation questions, and measure grounding and abstention on a larger labelled set before practical use.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
