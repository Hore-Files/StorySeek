# StorySeek Progress and Next Steps

Snapshot after the Gutenberg data migration, evaluation refresh, deploy setup, and frontend filter cleanup.

## Current State

StorySeek is now a working local IR prototype with three retrieval modes:

- BM25 lexical retrieval with boosted fields and metadata filters.
- Dense semantic retrieval using `sentence-transformers/all-MiniLM-L6-v2` and OpenSearch `knn_vector`.
- Hybrid retrieval using Reciprocal Rank Fusion over BM25 and dense results.

The primary UI is the React/Vite app in `frontend-react/`. The Streamlit app remains available as a legacy fallback. The backend is FastAPI, stateless, and backed by OpenSearch.

The deployed demo is available at `http://167.172.88.176:8080/`. The active demo corpus is now Project Gutenberg-derived data, not the original synthetic sample.

## Completed

### Retrieval and Backend

- `POST /search` supports `bm25`, `dense`, and `hybrid` modes.
- `/works/{work_id}` returns work detail records without internal indexing fields.
- `/similar/{work_id}` uses dense vectors when embeddings are available and falls back to text similarity if needed.
- `/facets` returns filter values from the active OpenSearch index, so the UI follows the currently indexed corpus.
- Content-warning exclusion is implemented as a hard OpenSearch `must_not` constraint.
- Trope/theme include filters use AND semantics, matching the UI labels.
- Query explanations are deterministic and rule-based.

### Indexing and Data

- Legacy synthetic dataset: `data/sample/works.jsonl` with 300 deterministic records.
- Current Gutenberg dataset: `data/sample/works_gutenberg.jsonl` with 500 Project Gutenberg-derived work-level records.
- Dataset selection is configurable through `DATA_PATH`, including Docker Compose and deployment scripts.
- Current indexing is work-level only. Raw Gutenberg text is stripped before records are sent to OpenSearch.
- Evaluation data now includes a small Gutenberg query set and LLM-assisted pooled qrels:
  - `data/eval/gutenberg_queries.jsonl`
  - `data/eval/gutenberg_qrels.csv`
- Index mapping includes both lexical fields and a 384-dimensional vector field.
- Index rebuilds use a versioned index name and atomically swap the `storyseek_works` search alias.
- Failed rebuilds should not break the currently searchable alias.

### Frontend

- React/Vite frontend is the main UI.
- Supports search, mode selection, filters, warning exclusion, pagination, dark mode, result cards, explanations, and "More Like This".
- Result cards now show source and work IDs, making it easy to verify whether results come from Project Gutenberg (`g_*`) or legacy synthetic data (`w_*`).
- Filter options are loaded from the backend `/facets` endpoint, with static fallback values only if the endpoint is unavailable.
- Streamlit UI is still present as a legacy demo surface.

### Reproducibility and Local Stack

- Python runtime is standardized on Python 3.12.
- Backend requirements include FastAPI, OpenSearch client, `httpx`, pytest, Streamlit, and sentence-transformers.
- Docker Compose now defines OpenSearch, indexer, API, and frontend services.
- Pytest collection is scoped to `backend/tests`, so utility scripts are not collected as tests.

### Evaluation and Load Testing

- `scripts/run_eval.py` compares BM25, dense, and hybrid retrieval with nDCG@10, MRR@10, and Recall@20.
- `scripts/run_eval.py` supports custom query, qrels, metrics, and comparison output paths.
- Latest Gutenberg evaluation artifacts:
  - `reports/gutenberg_metrics.json`
  - `reports/gutenberg_comparison.md`
- Latest Gutenberg prototype results:
  - BM25: nDCG@10 0.7492, MRR@10 1.0000, Recall@20 0.7303
  - Dense: nDCG@10 0.8040, MRR@10 1.0000, Recall@20 0.7830
  - Hybrid: nDCG@10 0.8082, MRR@10 1.0000, Recall@20 1.0000
- `scripts/load_test.py` runs lightweight concurrent local load tests.
- `reports/load_test_results.md` contains local prototype load-test evidence.

### CI/CD and Deployment

- GitHub Actions runs backend tests and frontend lint/build checks.
- Main-branch deploy uses SSH to a VPS and runs Docker Compose.
- Production compose serves the frontend on port `8080` because port `80` was already in use on the VPS.
- Deployment pulls Git LFS data when `git-lfs` is available on the server.

## Current Progress Estimate

- Local MVP retrieval system: about 80-85 percent complete.
- Full course deliverable: about 65-70 percent complete.

The main missing pieces are text-cleaning and passage/chunk indexing, stronger relevance evidence, final deployment hardening, and demo/video walkthrough polish.

## Recommended Next Commits

1. Prepare text cleaning before chunking:
   - remove Project Gutenberg header/footer/license boilerplate from raw text
   - normalize whitespace
   - keep the cleaner as a pure tested utility
   - do not change indexing behavior until the cleaner is verified

2. Add passage/chunk indexing behind a small, reversible path:
   - create chunk records from cleaned Gutenberg text
   - preserve work-level search behavior until passage retrieval is validated
   - document how work-level and passage-level indexes relate

3. Improve evaluation evidence:
   - expand qrels with a defensible judged subset
   - document that current Gutenberg qrels are LLM-assisted pooled judgments, not official human annotations
   - rerun BM25, dense, and hybrid after any passage-indexing change

4. Final course polish:
   - write demo video script
   - add deployment notes and rollback notes
   - refresh load-test evidence after the final indexing shape is stable

## Known Limits

- The original corpus is synthetic and intentionally metadata-rich, but the active demo corpus now uses Project Gutenberg-derived works.
- Current search indexes work-level metadata and summaries. Passage/chunk retrieval is not implemented yet.
- Current Gutenberg qrels are LLM-assisted pooled judgments. They are useful prototype evidence, not an official human-labeled benchmark.
- The raw Gutenberg text still needs boilerplate cleanup before chunking.
- OpenSearch runs as a single node locally; production scale is described as an architecture path, not claimed as proven capacity.
- Dense query embedding runs inside the API process for the MVP. A production version should move this to a dedicated inference service or shared cache if traffic grows.
