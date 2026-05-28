# Scalability

StorySeek is designed as a shared-corpus retrieval system: many users search the same catalog concurrently, while indexing happens offline.

## What Is Implemented Now

- Stateless FastAPI backend.
- OpenSearch as the single retrieval store for BM25 fields, metadata filters, and vector search.
- Versioned index rebuilds with alias swap, so a failed rebuild does not replace the active search index.
- Separate Gutenberg chunk index for passage/content retrieval.
- Query-side embedding cache inside each API process.
- Docker Compose stack with OpenSearch, work indexer, chunk indexer, API, and frontend.
- Lightweight request logging with path, status, latency, and search result metadata.
- Local load-test script for prototype p50/p95 latency evidence.

## Read Scaling Model

- API replicas can be increased because no user session or catalog state lives in the process.
- OpenSearch replicas can increase read throughput and availability.
- Metadata filters are pushed down to OpenSearch so ranking runs over fewer candidates.
- Pagination avoids returning the full result set.

Local development uses one OpenSearch node with 1 primary shard and 0 replicas. Production should use multiple data nodes, replicas, and shard sizing based on corpus size and query traffic.

## Dense Retrieval Scaling

Work and chunk embeddings are computed offline during indexing. Query embeddings are computed at request time and cached in memory.

This is acceptable for the MVP. For heavier traffic, move query embedding to one of:

- a dedicated embedding service,
- an ONNX or optimized inference runtime,
- a shared Redis-backed embedding cache,
- a precomputed popular-query cache.

## Full-Text Dataset Strategy

The Project Gutenberg dataset includes raw full text. StorySeek keeps large books out of the work index and uses a separate chunk index:

- `storyseek_works`: one document per work with metadata, summary, tags, and work-level embedding.
- `storyseek_chunks`: many chunk documents per work, each with chunk text, chunk position, `work_id`, and an embedding.
- Search passages first with BM25/dense/hybrid, aggregate top chunks by `work_id`, then return work-level results with optional matched snippets.

This keeps large books out of single-document scoring and makes dense retrieval more meaningful because embeddings represent short passages rather than entire works.

## Indexing and Rebuilds

The work indexer writes to a new versioned index and swaps the alias only after document count validation succeeds. This gives a simple rollback path: the previous versioned work index can be kept and the alias can be moved back manually if needed.

The chunk indexer rebuilds `storyseek_chunks` from `data/processed/gutenberg_chunks.jsonl`. This is currently a simpler full rebuild because chunks are generated offline and committed for deploy convenience.

Future improvements:

- partial updates,
- batch checkpoints,
- explicit old-index retention policy,
- CI or scheduled rebuild job.

## Load Testing

`scripts/load_test.py` sends concurrent requests to `POST /search` and writes `reports/load_test_results.md`. For the current frontend path, refresh load evidence against `/search-content` after the deploy is verified.

Recommended command:

```bash
python scripts/load_test.py --modes bm25 hybrid --concurrency 10 50 100
```

The report should include environment details: CPU/RAM, Python version, OpenSearch heap, dataset size, and backend worker count. Current results should be presented as local prototype evidence, not production capacity guarantees.

## Main Bottlenecks

1. Query embedding latency for dense/hybrid modes.
2. OpenSearch vector index memory and kNN candidate count.
3. Single-node OpenSearch in local development.
4. Backend JSON serialization for large result pages.
5. Browser/UI rendering if result cards become too dense.
