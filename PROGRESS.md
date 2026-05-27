# StorySeek Progress and Next Steps

Snapshot after the scalability and SWE hardening pass.

## Current State

StorySeek is now a working local IR prototype with three retrieval modes:

- BM25 lexical retrieval with boosted fields and metadata filters.
- Dense semantic retrieval using `sentence-transformers/all-MiniLM-L6-v2` and OpenSearch `knn_vector`.
- Hybrid retrieval using Reciprocal Rank Fusion over BM25 and dense results.

The primary UI is the React/Vite app in `frontend-react/`. The Streamlit app remains available as a legacy fallback. The backend is FastAPI, stateless, and backed by OpenSearch.

## Completed

### Retrieval and Backend

- `POST /search` supports `bm25`, `dense`, and `hybrid` modes.
- `/works/{work_id}` returns work detail records without internal indexing fields.
- `/similar/{work_id}` uses dense vectors when embeddings are available and falls back to text similarity if needed.
- Content-warning exclusion is implemented as a hard OpenSearch `must_not` constraint.
- Trope/theme include filters use AND semantics, matching the UI labels.
- Query explanations are deterministic and rule-based.

### Indexing and Data

- Synthetic dataset: `data/sample/works.jsonl` with 300 deterministic records.
- Evaluation data: 8 queries and 963 rule-derived qrels judgments.
- Index mapping includes both lexical fields and a 384-dimensional vector field.
- Index rebuilds use a versioned index name and atomically swap the `storyseek_works` search alias.
- Failed rebuilds should not break the currently searchable alias.

### Frontend

- React/Vite frontend is the main UI.
- Supports search, mode selection, filters, warning exclusion, pagination, dark mode, result cards, explanations, and "More Like This".
- Streamlit UI is still present as a legacy demo surface.

### Reproducibility and Local Stack

- Python runtime is standardized on Python 3.12.
- Backend requirements include FastAPI, OpenSearch client, `httpx`, pytest, Streamlit, and sentence-transformers.
- Docker Compose now defines OpenSearch, indexer, API, and frontend services.
- Pytest collection is scoped to `backend/tests`, so utility scripts are not collected as tests.

### Evaluation and Load Testing

- `scripts/run_eval.py` compares BM25, dense, and hybrid retrieval with nDCG@10, MRR@10, and Recall@20.
- `scripts/load_test.py` runs lightweight concurrent local load tests.
- `reports/load_test_results.md` contains local prototype load-test evidence.

## Current Progress Estimate

- Local MVP retrieval system: about 65-70 percent complete.
- Full course deliverable: about 50-55 percent complete.

The main missing pieces are fresh evaluation artifacts, full clean test run in a fresh environment, frontend build/lint proof, hosted demo, and video walkthrough.

## Recommended Next Commits

1. Run and commit evaluation outputs:
   - `python scripts/run_eval.py --modes bm25 dense hybrid`
   - commit `reports/metrics.json` and `reports/comparison.md`

2. Validate reproducibility:
   - fresh Python 3.12 venv
   - `python -m pytest -q`
   - `npm run build` and `npm run lint` in `frontend-react`

3. Refresh load-test evidence:
   - `python scripts/load_test.py --modes bm25 hybrid`
   - update `reports/load_test_results.md` with environment details.

4. Final course polish:
   - add hosted demo
   - write demo video script
   - add a small hand-labeled qrels subset if time allows

## Known Limits

- The corpus is synthetic and intentionally metadata-rich.
- Qrels are rule-derived, not human-labeled.
- OpenSearch runs as a single node locally; production scale is described as an architecture path, not claimed as proven capacity.
- Dense query embedding runs inside the API process for the MVP. A production version should move this to a dedicated inference service or shared cache if traffic grows.
