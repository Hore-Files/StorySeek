# Scalability

StorySeek is a **shared-corpus retrieval system**: many users search the same fiction catalog concurrently. The system is designed so that scaling read throughput is independent of dataset growth.

## Concurrency model

- **Stateless backend.** Each FastAPI process holds only a singleton OpenSearch client. Any request can be served by any replica. Add backend replicas behind a load balancer to scale request handling linearly.
- **Single source of truth in OpenSearch.** No per-user catalog state lives in the API process.
- **No login / user state in MVP.** Removes a class of horizontal-scaling blockers.

## Index throughput

OpenSearch handles read concurrency via shards and replicas:

- **Primary shards** partition the corpus; each shard can serve queries in parallel.
- **Replica shards** serve additional concurrent reads of the same data, and provide failover.
- Tuning for tonight's MVP: 1 primary, 0 replicas (single node). Production target: 3 primaries, 1–2 replicas, sized to RAM-fit hot shards.

## Filter pushdown reduces work

Facet filters (`format`, `genres`, `status`, …) and `must_not` content-warning exclusions run as `bool.filter` / `must_not` clauses, which are cached and applied **before** scoring. The BM25 scorer only sees the surviving documents.

## Pagination

`/search` accepts `page` and `size`. We never return the whole result set; large `from + size` would be replaced by `search_after` once corpora grow past 10k results.

## Caching opportunities

- **Query-embedding cache.** When dense retrieval lands, embeddings for repeat queries are cached (LRU keyed by normalized query string). Expected hit rate is high because users phrase trope-heavy queries similarly.
- **Result cache.** Popular `(query, filters)` combinations can be cached at the FastAPI layer or behind a reverse proxy.
- **OpenSearch's own filter cache** handles repeated filter predicates automatically.

## Indexing

Indexing is a batch job (`scripts/build_index.py`) decoupled from serving. As the catalog grows we can:

- Switch to streaming bulk ingest from an upstream pipeline.
- Run reindex jobs with zero downtime via alias swap.

## Embeddings (planned)

The dense path will compute query embeddings online (one model invocation per request, cached) and pre-compute document embeddings at index time. Document embedding generation is offline and embarrassingly parallel.

## Load testing plan

A future `scripts/load_test.py` (Locust or k6) will measure p50/p95 latency at:

- 10, 50, 100, 250, 500 concurrent users
- BM25-only vs. hybrid

Results land in `reports/load_test_results.md`.

## Bottleneck checklist (where we look first when things slow down)

1. JVM heap / shard count on OpenSearch
2. Field-data cache pressure from large terms aggregations
3. Embedding model latency (move to GPU or onnxruntime)
4. Backend serialization (use `orjson` if needed)
5. Streamlit UI ↔ API round-trip count per render
