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

### FastAPI backend

The backend is stateless. Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service and OpenSearch health |
| `GET` | `/facets` | Dataset-aware filter options from the active index |
| `POST` | `/search` | Work-level BM25, dense, or hybrid search |
| `POST` | `/search-content` | Chunk-level BM25, dense, or hybrid search grouped by work |
| `GET` | `/works/{work_id}` | Work detail lookup |
| `GET` | `/similar/{work_id}` | Dense-vector similar works with text fallback |

Main modules:

- `config.py`: environment settings, including `OPENSEARCH_INDEX_ALIAS`.
- `opensearch_client.py`: OpenSearch client, work/chunk mappings, versioned index helpers, and alias swap helpers.
- `data_loader.py`: JSONL bulk-indexing with combined text and document embeddings.
- `chunk_loader.py`: Gutenberg chunk bulk-indexing with chunk embeddings.
- `embeddings.py`: sentence-transformer wrapper and query embedding cache.
- `search/bm25.py`: boosted lexical query builder.
- `search/dense.py`: OpenSearch kNN query builder.
- `search/hybrid.py`: Reciprocal Rank Fusion.
- `search/content.py`: chunk retrieval queries and grouping back to work-level hits.
- `search/explain.py`: deterministic explanation bullets.

## Search Flow

1. UI loads filter options from `/facets`, with static fallback options if the endpoint is unavailable.
2. UI sends `{ query, filters, exclude_warnings, mode, page, size }` to `/search-content`.
3. Backend builds one of three chunk retrieval paths:
   - `bm25`: multi-field BM25 query over passage text and metadata.
   - `dense`: query embedding plus OpenSearch kNN over chunk embeddings.
   - `hybrid`: BM25 and dense chunk results fused with RRF.
4. Backend groups chunk hits by `work_id`, loads work metadata from `storyseek_works`, applies work-level filters, and returns matched passages.
5. UI renders ranked work results, snippets from matched chunks, and optional similar-story traversal.

## Index Design

The API uses two indexes:

- `storyseek_works`: work-level alias for metadata, summaries, detail pages, facets, and "More Like This".
- `storyseek_chunks`: chunk-level index for content retrieval through `/search-content`.

The work indexer builds versioned indexes such as `storyseek_works_v20260527143000` and swaps the alias after a successful build. The chunk index is rebuilt as `storyseek_chunks`.

Indexed fields:

- `text`: `title`, `summary`, `combined_text`
- `keyword`: `work_id`, `creator`, `format`, `language`, `status`, `audience_rating`, `length_bucket`, `source`
- `keyword[]`: `genres`, `themes`, `tropes`, `relationship_dynamics`, `content_warnings`
- `knn_vector`: `embedding`, dimension 384, HNSW/Lucene cosine similarity

`combined_text` is built from title, summary, genres, themes, tropes, and relationship dynamics. It feeds document embeddings and lexical fallback similarity.

Raw full text from `works_gutenberg.jsonl` is converted into `data/processed/gutenberg_chunks.jsonl`. The work-level index drops raw `text` before writing to OpenSearch so search responses and stored document sources stay small.

Chunk fields:

- `keyword`: `chunk_id`, `work_id`, `book_id`, `source`
- `integer`: `chunk_index`
- `text`: `text_chunk`, `combined_text`
- `keyword[]`: `genres`, `themes`
- `knn_vector`: `embedding`, dimension 384, HNSW/Lucene cosine similarity

## Retrieval Methods

| Method | Status |
|---|---|
| BM25 multi-field | Implemented |
| Dense kNN | Implemented |
| Hybrid BM25 + Dense via RRF | Implemented |
| Gutenberg passage/chunk retrieval | Implemented |

No LLM is in the retrieval critical path. Search ranking is performed by classical IR, vector retrieval, metadata filters, and rank fusion.
