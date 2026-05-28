# Deployment Notes

This document describes the intended production shape. The current project is still a local prototype.

## Recommended Shape

- Static frontend host for `frontend-react/`.
- Stateless FastAPI API replicas behind a load balancer.
- Managed OpenSearch or Elasticsearch cluster for BM25, metadata filters, and vector search.
- Batch indexing job that builds a versioned index and swaps the search alias after validation.
- Shared cache, such as Redis, for popular query embeddings and hot result sets if traffic grows.

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENSEARCH_URL` | OpenSearch or Elasticsearch endpoint. |
| `OPENSEARCH_INDEX_ALIAS` | Stable alias searched by the API. |
| `OPENSEARCH_USERNAME` | Optional search backend username. |
| `OPENSEARCH_PASSWORD` | Optional search backend password. |
| `EMBEDDING_MODEL_NAME` | Sentence-transformer model for dense retrieval. |
| `DATA_PATH` | Dataset path used by the indexer container. |
| `VITE_BACKEND_URL` | Browser-facing API URL for the React app. |

## Operational Notes

- Keep indexing separate from request serving.
- Do not swap the alias until document count validation passes.
- Keep at least one previous versioned index during demos so rollback is possible.
- Install `git-lfs` on the VPS before using `data/sample/works_gutenberg.jsonl` in `DATA_PATH`.
- Treat local load-test numbers as prototype evidence, not a production capacity claim.
- If dense query latency dominates, move embedding inference to a dedicated service or shared cache.
