# Gutenberg Adapter and Content Retrieval

StorySeek now uses Project Gutenberg as a real public-domain fiction source while keeping the existing backend `Work` contract stable.

Current production/demo dataset flow:

- `data/sample/works_gutenberg.jsonl`: canonical 500-book Gutenberg work dataset used for metadata, summaries, detail pages, and work-level OpenSearch indexing.
- `data/processed/gutenberg_chunks.jsonl`: generated passage/chunk dataset used for content-based retrieval.
- `storyseek_works`: work-level OpenSearch alias/index.
- `storyseek_chunks`: chunk-level OpenSearch index.
- `POST /search-content`: primary frontend search endpoint.

The frontend no longer exposes a separate Metadata/Content toggle. Users only choose retrieval mode (`bm25`, `dense`, or `hybrid`), and search runs through the combined content + metadata flow.

## Work-Level Dataset

The canonical work file is:

```powershell
data/sample/works_gutenberg.jsonl
```

Each row remains compatible with the backend `Work` schema:

- `work_id`
- `title`
- `creator`
- `format`
- `summary`
- `genres`
- `themes`
- `tropes`
- `relationship_dynamics`
- `content_warnings`
- `audience_rating`
- `status`
- `length_bucket`
- `language`
- `source`
- optional `release_date`
- full raw book text in `text`

Important implementation detail: `text` is kept in the JSONL file, but it is not stored in the work index. `backend/app/data_loader.py` strips raw full-text fields such as `text`, `content`, and `full_text` before bulk indexing to avoid oversized OpenSearch bulk requests.

## Release Dates

Release dates can be merged from the HuggingFace `fiction_books` metadata into the local work file:

```powershell
python scripts/add_gutenberg_release_dates.py --in-place
```

This creates a backup:

```powershell
data/sample/works_gutenberg.jsonl.bak
```

Do not commit the `.bak` file unless explicitly needed.

After changing `works_gutenberg.jsonl`, rebuild the work index:

```powershell
python scripts/build_index.py --recreate --path data/sample/works_gutenberg.jsonl
```

## Build Work Index

```powershell
python scripts/build_index.py --recreate --path data/sample/works_gutenberg.jsonl
```

The script builds a versioned concrete index such as `storyseek_works_vYYYYMMDDHHMMSS`, verifies the indexed count, then atomically moves the `storyseek_works` alias to the new index.

This avoids deleting `storyseek_works` when it is an alias.

## Generate Content Chunks

The current default chunk strategy reads from the local fixed work file, not directly from HuggingFace chunks:

```powershell
python scripts/convert_gutenberg_chunks.py
```

Default behavior:

- source: `data/sample/works_gutenberg.jsonl`
- output: `data/processed/gutenberg_chunks.jsonl`
- book limit: 500
- max chunks per book: 100
- chunk size: 5 sentences
- overlap: 1 sentence
- boilerplate/noise chunks are filtered

Useful alternatives:

```powershell
python scripts/convert_gutenberg_chunks.py --book-limit 100 --max-chunks-per-book 50
python scripts/convert_gutenberg_chunks.py --source data/sample/works_gutenberg.jsonl
python scripts/convert_gutenberg_chunks.py --from-hf-chunks
```

The generated chunk file is intentionally committed for VPS/deploy convenience in the current project setup.

## Build Chunk Index

```powershell
python scripts/build_chunk_index.py --recreate
```

Expected current demo size:

```text
48730 chunks
```

The chunk index stores:

- `chunk_id`
- `work_id`
- `book_id`
- `chunk_index`
- `title`
- `creator`
- `genres`
- `themes`
- `text_chunk`
- `combined_text`
- `embedding`

## Search Flow

Frontend search calls:

```text
POST /search-content
```

The backend searches `storyseek_chunks`, then groups chunk hits by `work_id`, loads the corresponding work from `storyseek_works`, and returns one result per book with matched passages.

Retrieval modes:

- `bm25`: lexical search over chunk text and metadata.
- `dense`: embedding search over chunk content.
- `hybrid`: Reciprocal Rank Fusion over BM25 and dense chunk results.

Response highlights:

- `work`: normal StorySeek `Work` object.
- `matched_passages`: best matching chunks for the book.
- `score`: retrieval score.

## Project Gutenberg Source Link

`StoryDetails.jsx` builds the source link from `book_id` when available, otherwise from numeric suffixes in `work_id`, e.g.:

```text
g_01400 -> https://www.gutenberg.org/ebooks/1400
```

Leading zeroes are stripped before creating the URL.

## Evaluation

Generate Gutenberg qrels:

```powershell
python scripts/generate_eval_qrels_gutenberg.py
```

Run evaluation:

```powershell
python scripts/run_eval.py `
  --queries data/eval/queries_gutenberg.jsonl `
  --qrels data/eval/qrels_gutenberg.csv `
  --out reports/metrics_gutenberg.json `
  --comparison-out reports/comparison_gutenberg.md
```

The evaluation report notes Gutenberg-specific qrels separately from the synthetic baseline.

## Frontend Setup

Frontend runs on port `3001`:

```powershell
cd frontend-react
npm install
npm.cmd run dev
```

Open:

```text
http://localhost:3001
```

The frontend expects the backend at:

```text
http://localhost:8000
```

Override with:

```env
VITE_BACKEND_URL=http://localhost:8000
```

## Recommended Local Verification

```powershell
python scripts/build_index.py --recreate --path data/sample/works_gutenberg.jsonl
python scripts/build_chunk_index.py --recreate
uvicorn backend.app.main:app --reload --port 8000
```

Then in another terminal:

```powershell
cd frontend-react
npm.cmd run lint
npm.cmd run build
npm.cmd run dev
```

Backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
```

Current passing baseline:

```text
29 backend tests passing
frontend lint clean
frontend build passing
```
