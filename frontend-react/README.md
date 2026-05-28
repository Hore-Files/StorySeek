# StorySeek React Frontend

Primary StorySeek UI built with React, Vite, and the local design tokens in `src/index.css`.

The frontend now uses one combined search flow. Users only choose the retrieval method (`bm25`, `dense`, or `hybrid`); the app sends searches to the backend content endpoint so results can include Gutenberg metadata and matched passages.

## Prerequisites

- Node.js 18 or newer
- npm
- OpenSearch running locally
- StorySeek FastAPI backend running at `http://localhost:8000`
- Work index built from `data/sample/works_gutenberg.jsonl`
- Chunk index built from `data/processed/gutenberg_chunks.jsonl`

## Backend Setup Needed First

From the repository root, make sure the backend indexes are ready:

```powershell
python scripts/build_index.py --recreate --path data/sample/works_gutenberg.jsonl
python scripts/build_chunk_index.py --recreate
uvicorn backend.app.main:app --reload --port 8000
```

If `data/processed/gutenberg_chunks.jsonl` does not exist yet, generate it first:

```powershell
python scripts/convert_gutenberg_chunks.py
```

## Frontend Setup

From the repository root:

```powershell
cd frontend-react
npm install
npm.cmd run dev
```

Open:

```text
http://localhost:3001
```

The Vite dev server port is configured in `vite.config.js`.

## Backend URL

By default, the frontend calls:

```text
http://localhost:8000
```

To use a different backend URL for a one-off local run, set `VITE_BACKEND_URL` in the shell before starting Vite:

```powershell
$env:VITE_BACKEND_URL = "http://localhost:8000"
npm.cmd run dev
```

Production builds receive `VITE_BACKEND_URL` through Docker build args and GitHub Actions secrets.

## Build and Lint

```powershell
npm.cmd run build
npm.cmd run lint
```

Use `npm.cmd` on Windows PowerShell if `npm` has execution-policy issues.

## Common Fixes

If Vite shows a PostCSS/native binding error, reinstall frontend dependencies:

```powershell
cd frontend-react
Remove-Item -Recurse -Force node_modules
npm install
npm.cmd run dev
```

If search returns backend errors, check that both indexes exist:

```powershell
curl http://localhost:9200/storyseek_works/_count
curl http://localhost:9200/storyseek_chunks/_count
curl http://localhost:8000/health
```

## Important Files

- `src/App.jsx`: main search page, filters, retrieval mode selection, pagination, details state, and backend calls.
- `src/components/StoryCard.jsx`: result cards with metadata, warnings, matched passage, explanations, and actions.
- `src/components/StoryDetails.jsx`: detailed work view with summary, release date, Project Gutenberg source link, tags, and matched passages.
- `src/components/SimilarStories.jsx`: dense-similarity recommendation view.
- `src/index.css`: theme tokens, responsive layout, dark mode, result cards, and detail page styles.
- `vite.config.js`: Vite dev-server configuration; current port is `3001`.
