# StorySeek

StorySeek is a trope-aware retrieval system for discovering fiction works through natural-language descriptions, metadata filters, and semantic similarity. It is built for an Information Retrieval / Web Search course project in Category A: Project / System Development.

The system is a search and discovery layer over a fiction catalog. It is not a reading platform and does not scrape copyrighted archives.

## Team Members

| Name | Student ID |
|---|---|
| Muhammad Farid Hasabi | 2306152512 |
| Utandra Nur Ahmad Jais | 2306152443 |
| Muhammad Wendy Fyfo Anggara | 2306223906 |
| Muhammad Fayyed As Shidqi | 2306230395 |

## Implemented Features

- BM25 keyword search with field boosts over title, summary, genres, themes, tropes, relationships, and combined text.
- Dense semantic search with `sentence-transformers/all-MiniLM-L6-v2` and OpenSearch `knn_vector`.
- Hybrid search using Reciprocal Rank Fusion over BM25 and dense rankings.
- Faceted filters for format, genre, trope, theme, status, audience rating, length, language, and content-warning exclusion.
- Rule-based "Why this matched" explanations.
- Semantic "More Like This" endpoint using stored document embeddings, with text fallback.
- React + Vite frontend as the primary UI; Streamlit remains as a legacy fallback.
- Evaluation harness for nDCG@10, MRR@10, and Recall@20.
- Local load test script and prototype load test report.
- Docker Compose stack for OpenSearch, backend, indexer, and frontend.

## Architecture

```text
+------------------+       HTTP/JSON       +---------------+       OpenSearch DSL / kNN       +----------------+
| React Frontend   | --------------------> | FastAPI API   | ------------------------------> | OpenSearch 2.x |
| Vite, port 3001  | <-------------------- | Stateless     | <------------------------------ | BM25 + vectors |
+------------------+                       +---------------+                                  +----------------+
```

- `frontend-react/`: primary UI for search, filters, pagination, dark mode, and similar-story traversal.
- `backend/app/`: FastAPI service, retrieval query builders, embeddings, index client, and schemas.
- `scripts/build_index.py`: versioned index builder with alias swap for safer rebuilds.
- `data/sample/works.jsonl`: deterministic synthetic catalog with 300 works.
- `data/eval/`: evaluation queries and rule-derived qrels.

See `docs/architecture.md`, `docs/scalability.md`, `docs/evaluation.md`, and `docs/deployment.md` for details.

## Quickstart: Docker Compose

Prerequisites: Docker Desktop.

```bash
docker compose up --build
```

This starts:

- OpenSearch on http://localhost:9200
- one-shot indexer that builds a versioned index and swaps the `storyseek_works` alias
- FastAPI on http://localhost:8000
- React UI on http://localhost:3001

The first run can take several minutes because the backend image installs ML dependencies and the indexer downloads the embedding model.

## Quickstart: Local Development

Prerequisites: Python 3.12, Node.js 18+, Docker Desktop.

```powershell
docker compose up -d opensearch

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt

python scripts\build_index.py --recreate
uvicorn backend.app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend-react
npm install
npm run dev -- --host 127.0.0.1 --port 3001
```

Open:

- React UI: http://localhost:3001
- API docs: http://localhost:8000/docs

Optional legacy UI:

```powershell
streamlit run frontend\streamlit_app.py
```

## Evaluation and Load Test

Run retrieval evaluation after OpenSearch is indexed and the backend is running:

```bash
python scripts/run_eval.py --modes bm25 dense hybrid
```

This writes:

- `reports/metrics.json`
- `reports/comparison.md`

Run local prototype load testing:

```bash
python scripts/load_test.py --modes bm25 hybrid
```

This writes `reports/load_test_results.md`. These results are local prototype evidence, not production capacity guarantees.

## Configuration

Copy `.env.example` to `.env` if you want to override defaults.

| Variable | Default | Purpose |
|---|---|---|
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch endpoint for local backend |
| `OPENSEARCH_INDEX_ALIAS` | `storyseek_works` | Search alias used by API and indexer |
| `OPENSEARCH_USERNAME` | empty | Optional OpenSearch username |
| `OPENSEARCH_PASSWORD` | empty | Optional OpenSearch password |
| `BACKEND_URL` | `http://localhost:8000` | Used by legacy Streamlit |
| `VITE_BACKEND_URL` | `http://localhost:8000` | Used by React frontend |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Dense retrieval model |

## Notes for Graders

- StorySeek is fundamentally an IR system: BM25, dense retrieval, metadata filters, and rank fusion are the core path.
- No LLM is required for search or explanation.
- The current dataset is synthetic by design because trope, relationship, status, and content-warning metadata are central to the project.
- Evaluation qrels are rule-derived from metadata and should be treated as reproducible prototype evidence, not a benchmark-grade human-labeled dataset.
