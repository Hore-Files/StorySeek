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
- Gutenberg content search over passage chunks, grouped back to work-level results with matched passages.
- Dataset-aware faceted filters for format, genre, trope, theme, status, audience rating, length, language, and content-warning exclusion.
- Rule-based "Why this matched" explanations.
- Semantic "More Like This" endpoint using stored document embeddings, with text fallback.
- React + Vite frontend as the primary UI; Streamlit remains as a legacy fallback.
- Evaluation harness for nDCG@10, MRR@10, and Recall@20.
- Local load test script and prototype load test report.
- Docker Compose stack for OpenSearch, backend, work indexer, chunk indexer, and frontend.

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
- `scripts/build_chunk_index.py`: chunk index builder for Gutenberg passage retrieval.
- `data/sample/works.jsonl`: deterministic synthetic catalog with 300 works.
- `data/sample/works_gutenberg.jsonl`: Project Gutenberg catalog stored with Git LFS.
- `data/processed/gutenberg_chunks.jsonl`: generated Gutenberg passage chunks.
- `data/eval/`: evaluation queries and rule-derived qrels.

See `docs/architecture.md`, `docs/scalability.md`, `docs/evaluation.md`, and `docs/deployment.md` for details.

## Dataset
The dataset used in this project is sourced from:
- [Project Gutenberg Dataset](https://huggingface.co/datasets/Despina/project_gutenberg)
- [Gutendex](https://gutendex.com/)

## Quickstart: Docker Compose

Prerequisites: Docker Desktop.

```bash
docker compose up --build
```

This starts:

- OpenSearch on http://localhost:9200
- one-shot work indexer that builds a versioned index and swaps the `storyseek_works` alias
- one-shot chunk indexer that builds the `storyseek_chunks` content index
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

To rebuild the Project Gutenberg work index manually:

```powershell
python scripts\build_index.py --recreate --path data\sample\works_gutenberg.jsonl
```

To rebuild the Gutenberg chunk index manually:

```powershell
python scripts\build_chunk_index.py --recreate
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

For the Project Gutenberg corpus:

```bash
python scripts/run_eval.py \
  --endpoint /search-content \
  --queries data/eval/gutenberg_queries.jsonl \
  --qrels data/eval/gutenberg_qrels.csv \
  --out reports/gutenberg_metrics.json \
  --comparison-out reports/gutenberg_comparison.md \
  --modes bm25 dense hybrid
```

The Gutenberg qrels are LLM-assisted pooled judgments over BM25, dense, and hybrid candidates.

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
| `DATA_PATH` | `data/sample/works_gutenberg.jsonl` | Dataset path used by the work indexer in Docker |
| `OPENSEARCH_CHUNKS_INDEX` | `storyseek_chunks` | Chunk index used by `/search-content` |

## Notes for Graders

- StorySeek is fundamentally an IR system: BM25, dense retrieval, metadata filters, passage retrieval, and rank fusion are the core path.
- No LLM is required for search or explanation.
- The legacy synthetic dataset is retained for regression and demos, but the primary corpus is Project Gutenberg-derived.
- `works_gutenberg.jsonl` is indexed as work-level metadata, while `gutenberg_chunks.jsonl` powers content retrieval through `/search-content`.
- Synthetic evaluation qrels are rule-derived from metadata; Gutenberg qrels are LLM-assisted pooled judgments. Both should be treated as prototype evidence, not benchmark-grade human-labeled labels.
