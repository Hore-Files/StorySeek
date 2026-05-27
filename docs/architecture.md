# Architecture

## Components

```
+-----------+      HTTP/JSON       +----------+      OpenSearch DSL     +-------------+
| Streamlit | -------------------> | FastAPI  | ----------------------> | OpenSearch  |
|    UI     | <------------------- |  app     | <---------------------- |   2.x       |
+-----------+                      +----------+                         +-------------+
```

### Streamlit frontend (`frontend/streamlit_app.py`)
Thin client. Owns no state beyond Streamlit session. Renders search input, sidebar filters, retrieval mode radio (BM25, Dense, Hybrid), result cards, explanations, and "More like this" results. Calls FastAPI over HTTP.

### FastAPI backend (`backend/app/`)
Stateless service. Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Cluster and service liveness |
| `POST` | `/search` | Run BM25, Dense, or Hybrid retrieval with filters |
| `GET` | `/works/{work_id}` | Return a single record by id |
| `GET` | `/similar/{work_id}` | More-like-this over `combined_text` |

Modules:

- `config.py` - env-driven settings via `pydantic-settings`.
- `opensearch_client.py` - singleton `OpenSearch` client and `INDEX_MAPPING`.
- `schemas.py` - Pydantic models and retrieval mode contract.
- `data_loader.py` - JSONL bulk-index helpers, including `combined_text` and document embeddings.
- `embeddings.py` - sentence-transformer model wrapper and query embedding cache.
- `search/bm25.py` - `multi_match` query builder with boosts, filters, and content-warning exclusion.
- `search/dense.py` - OpenSearch kNN query builder over the `embedding` field.
- `search/hybrid.py` - Reciprocal Rank Fusion over BM25 and Dense rankings.
- `search/explain.py` - rule-based "why this matched" generator.

### OpenSearch
OpenSearch stores both lexical and vector retrieval fields in one index. The local dev deployment is a single-node cluster from `docker-compose.yml`; the production design scales with shards, replicas, and stateless API replicas.

## Request flow: `POST /search`

1. UI sends `{ query, filters, exclude_warnings, mode, page, size }`.
2. Backend chooses the retrieval path:
   - `bm25`: multi-field BM25 query with boosts.
   - `dense`: query embedding plus OpenSearch kNN.
   - `hybrid`: runs BM25 and Dense, then fuses rankings with Reciprocal Rank Fusion.
3. OpenSearch applies facet filters and content-warning `must_not` constraints.
4. Backend attaches rule-based explanations per hit.
5. JSON response returns ranked hits to the UI.

## Index design

Single index: `storyseek_works`.

- `text`: `title`, `summary`, `combined_text`
- `keyword`: `work_id`, `creator`, `format`, `language`, `status`, `audience_rating`, `length_bucket`, `source`
- `keyword[]`: `genres`, `themes`, `tropes`, `relationship_dynamics`, `content_warnings`
- `knn_vector`: `embedding`, dimension 384, HNSW/Lucene cosine similarity

`combined_text` is built from title, summary, genres, themes, tropes, and relationship dynamics. It feeds both `more_like_this` and document embeddings.

## Retrieval methods

| Method | Status | Where |
|---|---|---|
| BM25 multi-field | Implemented | `search/bm25.py` |
| Dense kNN | Implemented | `search/dense.py`, `embeddings.py` |
| Hybrid BM25 + Dense via RRF | Implemented | `search/hybrid.py` |

## Why this is an IR project, not an LLM wrapper

- Ranking is performed by BM25, dense vector similarity, and RRF. No LLM is in the retrieval critical path.
- Explanations are deterministic and rule-based.
- LLM/RAG can be added later as a post-retrieval summarizer, but it is not part of the core system.
