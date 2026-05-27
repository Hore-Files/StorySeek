# StorySeek

StorySeek is a trope-aware semantic search engine for fanfiction and transformative fiction archives. Inspired by how readers search on platforms like AO3 and Wattpad. Instead of relying on exact titles, authors, or rigid tag systems, it helps users discover stories through natural-language descriptions of themes, moods, tropes, and character dynamics.

## Team Members

| Name | Student ID |
|---|---|
| Muhammad Farid Hasabi | 2306152512 |
| Utandra Nur Ahmad Jais | 2306152443 |
| Muhammad Wendy Fyfo Anggara | 2306223906 |
| Muhammad Fayyed As Shidqi | 2306230395 |

## Course Context

This repository is our deliverable for the **Information Retrieval / Web Search** course (Category A: Project / System Development).

## Problem

Existing fiction discovery relies on exact titles, authors, or hand-picked tags. Readers usually know what kind of story they want (`"slow burn rivals to lovers with found family, no major character death"`) but not the exact terms a catalog uses. StorySeek is a search/discovery layer over a fiction catalog that matches not just on keywords, but also meaning, themes, and metadata.

## Features

- **3 Retrieval Modes:** BM25 (keyword), Dense (semantic embedding via `all-MiniLM-L6-v2`), and Hybrid (Reciprocal Rank Fusion)
- **Faceted Filters:** Format, Genre, Trope, Themes, Status, Audience Rating, and Content Warning exclusion
- **Dark Mode:** Full dark theme with smooth transitions based on Material Design 3 tokens
- **"Why This Matched":** Rule-based explanation for every search result
- **More Like This:** Similar story recommendations with infinite traversal (click More Like This from within the recommendation view)
- **Dynamic Pagination:** 5, 10, 20, or 50 results per page

## Architecture

```
+------------------+        +---------------+        +---------------------+
|  React Frontend  | -----> |   FastAPI     | -----> |     OpenSearch      |
|  (Vite + React)  | <----- |   Backend     | <----- |  (BM25, Dense,      |
+------------------+        +---------------+        |   Hybrid/RRF)       |
                                                     +---------------------+
```

- **Frontend:** `frontend-react/` — React 18 + Vite. Dark mode, filter sidebar, infinite recommendation traversal.
- **Backend:** `backend/app/` — FastAPI, stateless, horizontally scalable.
- **Index:** OpenSearch, single-node for dev, sharded/replicated in production.

See `docs/architecture.md`, `docs/data_schema.md`, and `docs/scalability.md` for details.

## Repository Layout

```
backend/             FastAPI app + OpenSearch client + retrieval logic
frontend-react/      React 18 + Vite (primary UI)
frontend/            Streamlit UI (legacy, still functional)
data/sample/         Synthetic fiction catalog (committed JSONL, 300 records)
scripts/             Synthetic data generation + index build
docs/                Architecture, schema, scalability writeups
docker-compose.yml   Single-node OpenSearch for dev
reports/             Evaluation metrics (nDCG, MRR, Recall)
```

## Dataset

The committed dataset is `data/sample/works.jsonl` with 300 deterministic synthetic records. This is the primary final dataset because the project needs trope-aware metadata, relationship dynamics, audience ratings, and content warnings that public-domain book catalogs usually do not provide.

To regenerate or expand it:

```bash
python scripts/generate_synthetic_data.py --count 1000 --seed 42
```

Real/public metadata from Project Gutenberg or Standard Ebooks is documented as a future dataset option in `docs/data_schema.md`.

---

##  Quickstart

**Prerequisites:** Python 3.10+, Node.js 18+, Docker Desktop.

### Step 1 — Start OpenSearch

```bash
docker compose up -d opensearch
```

Wait 30–60 seconds for OpenSearch to be ready. Verify: `curl http://localhost:9200`

### Step 2 — Set Up Backend

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# macOS / bash / zsh:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 3 — Build the Search Index

```bash
# (Optional) Regenerate synthetic dataset
python scripts/generate_synthetic_data.py --count 300 --seed 42

# Build the OpenSearch index (includes dense embeddings)
python scripts/build_index.py --recreate
```

> ⚠️ This step takes a few minutes as it generates sentence embeddings for 300 documents using `all-MiniLM-L6-v2`.

### Step 4 — Run the Backend API

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- API: **http://localhost:8000**
- Interactive docs: **http://localhost:8000/docs**

### Step 5 — Run the React Frontend (Recommended)

Open a **new terminal** (keep the backend terminal running):

```bash
cd frontend-react
npm install
npm run dev
```

App available at: **http://localhost:3001**

>  If the port differs, check your terminal output for the correct URL.

### (Optional) Run the Legacy Streamlit UI

```bash
streamlit run frontend/streamlit_app.py
# -> http://localhost:8501
```

---

## How to Use

1. **Select a retrieval mode** in the navbar: `bm25`, `dense`, or `hybrid`
2. **Type a story description** in the search bar (e.g. *"enemies to lovers fantasy with slow burn and political intrigue"*)
3. **Use the filter sidebar** to narrow results by genre, trope, status, audience, etc.
4. **Click "More Like This"** on any story card to see similar recommendations
5. **In the recommendation view**, click "More Like This" again to explore further (infinite traversal)
6. **Toggle dark mode** using the 🌙 icon in the top-right corner of the header

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch cluster endpoint |
| `OPENSEARCH_INDEX` | `storyseek_works` | Index name |
| `BACKEND_URL` | `http://localhost:8000` | Used by Streamlit (legacy) |
| `VITE_BACKEND_URL` | `http://localhost:8000` | Used by React frontend |

For the React frontend, create `frontend-react/.env`:

```env
VITE_BACKEND_URL=http://localhost:8000
```

---

## Notes

- Retrieval logic is OpenSearch DSL + Python — explainable as an IR system, not an LLM wrapper.
- LLMs are out of scope for the core retrieval path. Future RAG over results is optional.
- No copyrighted sources are scraped. The current dataset is synthetic; future ingest will use Project Gutenberg / Standard Ebooks metadata under their stated licenses.
