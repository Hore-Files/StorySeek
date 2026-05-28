# StorySeek Progress and Next Steps

Snapshot after the Gutenberg data migration, content chunk retrieval integration, deploy setup, and frontend filter cleanup.

## Current State

StorySeek is now a working IR prototype with three retrieval modes:

- BM25 lexical retrieval with boosted fields and metadata filters.
- Dense semantic retrieval using `sentence-transformers/all-MiniLM-L6-v2` and OpenSearch `knn_vector`.
- Hybrid retrieval using Reciprocal Rank Fusion over BM25 and dense results.

The primary UI is the React/Vite app in `frontend-react/`. The Streamlit app remains available as a legacy fallback. The backend is FastAPI, stateless, and backed by OpenSearch.

The deployed demo is available at `http://167.172.88.176:8080/`. The active demo corpus is Project Gutenberg-derived data, not the original synthetic sample.

## Completed

### Retrieval and Backend

- `POST /search` supports work-level `bm25`, `dense`, and `hybrid` modes.
- `POST /search-content` is the primary frontend search endpoint. It searches Gutenberg content chunks, groups results by `work_id`, loads work metadata, and returns matched passages.
- `/works/{work_id}` returns work detail records without internal indexing fields.
- `/similar/{work_id}` uses dense vectors when embeddings are available and falls back to text similarity if needed.
- `/facets` returns filter values from the active OpenSearch index, so the UI follows the currently indexed corpus.
- Content-warning exclusion is implemented as a hard OpenSearch `must_not` constraint.
- Trope/theme include filters use AND semantics, matching the UI labels.
- Query explanations are deterministic and rule-based.

### Indexing and Data

- Legacy synthetic dataset: `data/sample/works.jsonl` with 300 deterministic records.
- Current Gutenberg dataset: `data/sample/works_gutenberg.jsonl` with 500 Project Gutenberg-derived work-level records.
- Current Gutenberg chunk dataset: `data/processed/gutenberg_chunks.jsonl`, used by `/search-content`.
- Dataset selection is configurable through `DATA_PATH`, including Docker Compose and deployment scripts.
- Work-level indexing strips raw Gutenberg text before records are sent to OpenSearch.
- Chunk-level indexing stores cleaned passage chunks in `storyseek_chunks` with embeddings for content retrieval.
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
- Docker Compose now defines OpenSearch, work indexer, chunk indexer, API, and frontend services.
- Pytest collection is scoped to `backend/tests`, so utility scripts are not collected as tests.

### Evaluation and Load Testing

- `scripts/run_eval.py` compares BM25, dense, and hybrid retrieval with nDCG@10, MRR@10, and Recall@20.
- `scripts/run_eval.py` supports custom query, qrels, metrics, comparison output paths, and endpoint selection (`/search` or `/search-content`).
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
- Deployment builds both `storyseek_works` and `storyseek_chunks` before starting the API/frontend.
- Deployment pulls Git LFS data when `git-lfs` is available on the server.

## Current Progress Estimate

- Local MVP retrieval system: about 85-90 percent complete.
- Full course deliverable: about 70-75 percent complete.

The main missing pieces are production verification for chunk search, refreshed chunk-based evaluation artifacts, final load-test evidence, and demo/video walkthrough polish.

## Recommended Next Commits

1. Verify deployed chunk retrieval:
   - confirm `/api/search-content` returns `matched_passages`
   - confirm frontend cards show passage snippets
   - confirm `/api/works/{work_id}` works for returned Gutenberg IDs

2. Improve evaluation evidence:
   - expand qrels with a defensible judged subset
   - document that current Gutenberg qrels are LLM-assisted pooled judgments, not official human annotations
   - rerun BM25, dense, and hybrid against `/search-content`

3. Final course polish:
   - write demo video script
   - add deployment notes and rollback notes
   - refresh load-test evidence after the final indexing shape is stable

## Known Limits

- The original corpus is synthetic and intentionally metadata-rich, but the active demo corpus now uses Project Gutenberg-derived works.
- Current frontend search uses passage chunks grouped back to work-level results, but the qrels are still small and LLM-assisted.
- Current Gutenberg qrels are LLM-assisted pooled judgments. They are useful prototype evidence, not an official human-labeled benchmark.
- Chunk generation uses rule-based boilerplate filtering and sentence windows. It is good enough for prototype retrieval, but not a scholarly text edition pipeline.
- OpenSearch runs as a single node locally; production scale is described as an architecture path, not claimed as proven capacity.
- Dense query embedding runs inside the API process for the MVP. A production version should move this to a dedicated inference service or shared cache if traffic grows.
