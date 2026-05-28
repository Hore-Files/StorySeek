# Architecture

StorySeek is a shared-corpus retrieval system. Many users search the same fiction catalog through a stateless API backed by OpenSearch.

## Components

```text
+------------------+       HTTP/JSON       +---------------+       OpenSearch DSL / kNN       +----------------+
| React Frontend   | --------------------> | FastAPI API   | ------------------------------> | OpenSearch 2.x |
| Vite, port 3001  | <-------------------- | Stateless     | <------------------------------ | BM25 + vectors |
+------------------+                       +---------------+                                  +----------------+
```

### React frontend

`frontend-react/` is the primary UI. It renders search input, mode selection, filters, pagination, result cards, explanations, dark mode, and "More Like This" traversal. It calls FastAPI over HTTP.

`frontend/streamlit_app.py` is a legacy fallback UI.

### FastAPI backend

The backend is stateless. Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service and OpenSearch health |
| `GET` | `/facets` | Dataset-aware filter options from the active index |
| `POST` | `/search` | BM25, dense, or hybrid search |
| `GET` | `/works/{work_id}` | Work detail lookup |
| `GET` | `/similar/{work_id}` | Dense-vector similar works with text fallback |

Main modules:

- `config.py`: environment settings, including `OPENSEARCH_INDEX_ALIAS`.
- `opensearch_client.py`: OpenSearch client, mapping, versioned index helpers, and alias swap helpers.
- `data_loader.py`: JSONL bulk-indexing with combined text and document embeddings.
- `embeddings.py`: sentence-transformer wrapper and query embedding cache.
- `search/bm25.py`: boosted lexical query builder.
- `search/dense.py`: OpenSearch kNN query builder.
- `search/hybrid.py`: Reciprocal Rank Fusion.
- `search/explain.py`: deterministic explanation bullets.

## Search Flow

1. UI loads filter options from `/facets`, with static fallback options if the endpoint is unavailable.
2. UI sends `{ query, filters, exclude_warnings, mode, page, size }`.
3. Backend builds one of three retrieval paths:
   - `bm25`: multi-field BM25 query with boosts.
   - `dense`: query embedding plus OpenSearch kNN.
   - `hybrid`: BM25 and dense results fused with RRF.
4. OpenSearch applies metadata filters and content-warning exclusion.
5. Backend strips internal fields and attaches explanation bullets.
6. UI renders ranked results and optional similar-story traversal.

## Index Design

The API searches the alias `storyseek_works`. The indexer builds versioned indexes such as `storyseek_works_v20260527143000` and swaps the alias after a successful build.

Indexed fields:

- `text`: `title`, `summary`, `combined_text`
- `keyword`: `work_id`, `creator`, `format`, `language`, `status`, `audience_rating`, `length_bucket`, `source`
- `keyword[]`: `genres`, `themes`, `tropes`, `relationship_dynamics`, `content_warnings`
- `knn_vector`: `embedding`, dimension 384, HNSW/Lucene cosine similarity

`combined_text` is built from title, summary, genres, themes, tropes, and relationship dynamics. It feeds document embeddings and lexical fallback similarity.

Optional raw full text from `works_gutenberg.jsonl` is treated as source data for future passage indexing. The MVP work-level index drops the raw `text` field before writing to OpenSearch so search responses and stored document sources stay small.

## Retrieval Methods

| Method | Status |
|---|---|
| BM25 multi-field | Implemented |
| Dense kNN | Implemented |
| Hybrid BM25 + Dense via RRF | Implemented |

No LLM is in the retrieval critical path. Search ranking is performed by classical IR, vector retrieval, metadata filters, and rank fusion.
