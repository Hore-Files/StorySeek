# StorySeek

StorySeek is an Information Retrieval system for fiction discovery. It retrieves Project Gutenberg works from natural-language queries using lexical search, dense vector search, metadata filters, and hybrid rank fusion.

Live demo: https://storyseek.dev

## Team

| Name | Student ID |
|---|---|
| Muhammad Farid Hasabi | 2306152512 |
| Utandra Nur Ahmad Jais | 2306152443 |
| Muhammad Wendy Fyfo Anggara | 2306223906 |
| Muhammad Fayyed As Shidqi | 2306230395 |

## What It Implements

- BM25 retrieval with boosted fields.
- Dense retrieval with `sentence-transformers/all-MiniLM-L6-v2` and OpenSearch `knn_vector`.
- Hybrid retrieval with Reciprocal Rank Fusion.
- Passage-level Gutenberg content search via `storyseek_chunks`.
- Work-level metadata, facets, details, and "More Like This" via `storyseek_works`.
- React/Vite frontend and stateless FastAPI backend.
- Evaluation with nDCG@10, MRR@10, and Recall@20.
- Docker Compose stack for OpenSearch, indexers, API, and frontend.

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
- `data/sample/works_gutenberg.jsonl`: optional Project Gutenberg catalog stored with Git LFS.
- `data/eval/`: evaluation queries and rule-derived qrels.

See `docs/architecture.md`, `docs/scalability.md`, `docs/evaluation.md`, and `docs/deployment.md` for details.

## Run With Docker

Prerequisites: Docker Desktop and Git LFS data pulled.

```bash
docker compose up --build
```

Services:

- React UI: http://localhost:3001
- FastAPI: http://localhost:8000
- OpenSearch: http://localhost:9200

The first run can take several minutes because embeddings are generated for the work and chunk indexes.

## Local Development

```powershell
docker compose up -d opensearch

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt

python scripts\build_index.py --recreate --path data\sample\works_gutenberg.jsonl
python scripts\build_chunk_index.py --recreate
uvicorn backend.app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend-react
npm install
npm run dev -- --host 127.0.0.1 --port 3001
```

## Evaluation

Run the current chunk-based Gutenberg evaluation:

```bash
python scripts/run_eval.py \
  --backend https://storyseek.dev/api \
  --endpoint /search-content \
  --queries data/eval/gutenberg_queries.jsonl \
  --qrels data/eval/gutenberg_qrels.csv \
  --out reports/gutenberg_metrics.json \
  --comparison-out reports/gutenberg_comparison.md \
  --modes bm25 dense hybrid
```

Latest chunk-based results:

| Mode | mean nDCG@10 | mean MRR@10 | mean Recall@20 |
|---|---:|---:|---:|
| BM25 | 0.1958 | 0.4345 | 0.3010 |
| Dense | 0.4261 | 0.7470 | 0.5799 |
| Hybrid | 0.4221 | 0.7304 | 0.5058 |

The Gutenberg qrels are LLM-assisted pooled judgments, so the numbers are prototype evidence rather than benchmark-grade human annotations.

## Configuration

Runtime configuration is supplied through environment variables, Docker Compose, or GitHub Actions secrets. This repository intentionally does not track `.env` example files.

Important variables:

| Variable | Purpose |
|---|---|
| `OPENSEARCH_URL` | OpenSearch endpoint. |
| `OPENSEARCH_INDEX_ALIAS` | Work search alias, default `storyseek_works`. |
| `OPENSEARCH_CHUNKS_INDEX` | Chunk index, default `storyseek_chunks`. |
| `OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD` | Optional OpenSearch auth. |
| `EMBEDDING_MODEL_NAME` | Sentence-transformer model. |
| `DATA_PATH` | Work dataset path for the indexer. |
| `VITE_BACKEND_URL` | Browser-facing API URL for React builds. |

Deployment writes its runtime env file on the VPS from GitHub Actions secrets; no checked-in `.env` file is required.

## Notes

- Search and explanations do not require an LLM at runtime.
- The primary corpus is Project Gutenberg-derived; the synthetic dataset remains only as a legacy regression fixture.
- The production demo is a single-node VPS prototype, not a production benchmark.
- For deeper details, see `docs/architecture.md`, `docs/scalability.md`, `docs/evaluation.md`, and `docs/deployment.md`.
