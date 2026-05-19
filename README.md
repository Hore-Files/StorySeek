# StorySeek

StorySeek is a trope-aware semantic search engine for fanfiction and transformative fiction archives. Inspired by how readers search on platforms like AO3 and Wattpad. Instead of relying on exact titles, authors, or rigid tag systems, it helps users discover stories through natural-language descriptions of themes, moods, tropes, and character dynamics.

## Team Member:
- Muhammad Farid Hasabi (2306152512)
- Utandra Nur Ahmad Jais (2306152443)
- Muhammad Wendy Fyfo Anggara (2306223906)
- Muhammad Fayyed As Shidqi (2306230395)

## Course context

This repository is our deliverable for the **Information Retrieval / Web Search** course (Category A: Project / System Development).

## Problem

Existing fiction discovery relies on exact titles, authors, or hand-picked tags. Readers usually know what kind of story they want (`"slow burn rivals to lovers with found family, no major character death"`) but not the exact terms a catalog uses. StorySeek is a search/discovery layer over a fiction catalog that matches not just on keywords, but also meaning, themes, and metadata.

## MVP scope

- Unified `work` schema and synthetic dataset generator
- FastAPI backend on top of OpenSearch
- BM25 keyword retrieval with multi-field boosting
- Dense retrieval with sentence-transformers (`all-MiniLM-L6-v2`) + OpenSearch `knn_vector`
- Hybrid BM25 + dense ranking with Reciprocal Rank Fusion (RRF)
- Faceted filters (format, genre, status, length, audience rating, tropes)
- Hard constraint: exclude content warnings
- Rule-based "why this matched" explanation
- `/similar/{work_id}` via OpenSearch `more_like_this`
- Streamlit UI with search bar, filters, mode selector, result cards
- Single-node OpenSearch via `docker compose`
- Evaluation harness for nDCG@10, MRR@10, and Recall@20
- Lightweight API load-test script

### Dataset

The committed dataset is `data/sample/works.jsonl` with 300 deterministic synthetic records. This is the primary final dataset because the project needs trope-aware metadata, relationship dynamics, audience ratings, and content warnings that public-domain book catalogs usually do not provide.

To regenerate or expand it:

```bash
python scripts/generate_synthetic_data.py --count 1000 --seed 42
```

Real/public metadata from Project Gutenberg or Standard Ebooks is documented as a future dataset option in `docs/data_schema.md`.

### Final-deliverable roadmap

- End-to-end smoke run against a live OpenSearch cluster
- Evaluation results in `reports/metrics.json` and `reports/comparison.md`
- Load-test results in `reports/load_test_results.md`
- YouTube demo video, max 15 minutes
- Final English documentation pass

## Architecture

```
+-------------+        +---------------+        +---------------------+
|  Streamlit  | -----> |   FastAPI     | -----> |     OpenSearch      |
|     UI      | <----- |   backend     | <----- |   (BM25, dense,     |
+-------------+        +---------------+        |    hybrid search)   |
                                                +---------------------+
```

- **Frontend:** `frontend/streamlit_app.py` — stateless presentation only.
- **Backend:** `backend/app/` — FastAPI, stateless, horizontally scalable.
- **Index:** OpenSearch, single-node for dev, sharded/replicated in production.

See `docs/architecture.md`, `docs/data_schema.md`, and `docs/scalability.md` for details.

## Repository layout

```
backend/             FastAPI app + OpenSearch client + retrieval logic
frontend/            Streamlit UI
data/sample/         Synthetic fiction catalog (committed JSONL)
scripts/             Synthetic data generation + index build
docs/                Architecture, schema, scalability writeups
docker-compose.yml   Single-node OpenSearch for dev
```

## Quickstart

Prereqs: Python 3.10+, Docker Desktop.

```bash
# 1. Start OpenSearch
docker compose up -d opensearch

# 2. Install backend deps
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
# bash/zsh:   source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. (Optional) regenerate synthetic data
python scripts/generate_synthetic_data.py --count 300 --seed 42

# 4. Build the index
python scripts/build_index.py --recreate

# 5. Run the API
uvicorn backend.app.main:app --reload --port 8000
# -> http://localhost:8000/docs

# 6. Run the UI (new terminal)
streamlit run frontend/streamlit_app.py
# -> http://localhost:8501
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Purpose |
|---|---|---|
| `OPENSEARCH_URL` | `http://localhost:9200` | Cluster endpoint |
| `OPENSEARCH_INDEX` | `storyseek_works` | Index name |
| `BACKEND_URL` | `http://localhost:8000` | Used by Streamlit |

## Notes
- Retrieval logic is OpenSearch DSL + Python. Explainable as an IR system, not an LLM wrapper.
- LLMs are out of scope for the core retrieval path. Future RAG over results is optional.
- No copyrighted sources are scraped. The current dataset is synthetic; future ingest will use Project Gutenberg / Standard Ebooks metadata under their stated licenses.
