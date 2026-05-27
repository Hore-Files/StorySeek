# StorySeek React Frontend

This is the primary StorySeek UI, built with React, Vite, and the local design tokens in `src/index.css`.

## Prerequisites

- Node.js 18 or newer
- npm
- StorySeek FastAPI backend running at `http://localhost:8000`

## Run Locally

From the repository root:

```bash
cd frontend-react
npm install
npm run dev -- --host 127.0.0.1 --port 3001
```

Open http://localhost:3001.

If the backend URL is different, create `frontend-react/.env`:

```env
VITE_BACKEND_URL=http://localhost:8000
```

## Build and Lint

```bash
npm run build
npm run lint
```

## Important Files

- `src/App.jsx`: main search page, filters, mode selection, pagination, and dark mode.
- `src/components/StoryCard.jsx`: result cards with metadata, warnings, explanations, and "More Like This".
- `src/components/SimilarStories.jsx`: dense-similarity recommendation view.
- `src/index.css`: theme tokens and dark-mode overrides.
- `vite.config.js`: Vite dev-server configuration.
