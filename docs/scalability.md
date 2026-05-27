# Scalability

StorySeek is a shared-corpus retrieval system: many users search the same fiction catalog concurrently. The system is designed so read throughput can scale independently from dataset growth.

## Concurrency model

- **Stateless backend.** Each FastAPI process holds only an OpenSearch client and an embedding model cache. Any request can be served by any replica.
- **Single source of truth in OpenSearch.** No per-user catalog state lives in the API process.
- **No login or user state in the MVP.** This keeps horizontal scaling simple.

## OpenSearch scaling

OpenSearch handles read concurrency with shards and replicas:

- Primary shards partition the corpus and can serve queries in parallel.
- Replica shards serve additional reads and provide failover.
- Local MVP: 1 primary, 0 replicas on a single node.
- Production target: multiple primaries, 1-2 replicas, and hot shards sized to fit memory.

## Filter pushdown

Facet filters and content-warning exclusions run as `bool.filter` and `must_not` clauses. OpenSearch can cache and apply these before scoring, so BM25 and kNN ranking work on fewer candidate documents.

## Dense retrieval scaling

Document embeddings are computed offline during indexing. Query embeddings are computed online but cached with an LRU cache keyed by query text. Repeated trope-heavy searches should benefit from this cache.

As traffic grows, likely next steps are:

- Increase FastAPI replicas for BM25-heavy traffic.
- Move embedding inference to a dedicated service or ONNX runtime if query embedding latency dominates.
- Increase OpenSearch replicas for read-heavy workloads.

## Pagination

`/search` accepts `page` and `size`, and the API never returns the full result set. For very large corpora, deep pagination should move from `from`/`size` to `search_after`.

## Load testing

`scripts/load_test.py` runs concurrent requests against `POST /search` and writes `reports/load_test_results.md`.

Recommended local command:

```bash
python scripts/load_test.py --modes bm25 hybrid --concurrency 10 50 100
```

The report records p50, p95, max latency, request count, and success rate. These results are prototype evidence for the course deliverable, not production capacity guarantees.

## Bottleneck checklist

1. OpenSearch JVM heap and shard sizing
2. kNN candidate count and vector index memory
3. Query embedding latency
4. Backend JSON serialization
5. Streamlit to API round-trip count per render
