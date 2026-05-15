from __future__ import annotations

from functools import lru_cache

from opensearchpy import OpenSearch

from .config import get_settings

# Index mapping. `combined_text` is the catch-all field used by `more_like_this`
# today and (TODO) by the dense `knn_vector` field once embeddings land.
INDEX_MAPPING: dict = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "knn": True,
        },
        "analysis": {
            "analyzer": {
                "default": {"type": "standard"},
            }
        },
    },
    "mappings": {
        "properties": {
            "work_id": {"type": "keyword"},
            "title": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
            "creator": {"type": "keyword"},
            "format": {"type": "keyword"},
            "summary": {"type": "text"},
            "combined_text": {"type": "text"},
            "genres": {"type": "keyword"},
            "themes": {"type": "keyword"},
            "tropes": {"type": "keyword"},
            "relationship_dynamics": {"type": "keyword"},
            "content_warnings": {"type": "keyword"},
            "audience_rating": {"type": "keyword"},
            "status": {"type": "keyword"},
            "length_bucket": {"type": "keyword"},
            "language": {"type": "keyword"},
            "source": {"type": "keyword"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 384,
                "method": {
                    "name": "hnsw",
                    "engine": "lucene",
                    "space_type": "cosinesimil",
                },
            },
        }
    },
}


def build_combined_text(doc: dict) -> str:
    parts = [
        doc.get("title", ""),
        doc.get("summary", ""),
        " ".join(doc.get("genres", [])),
        " ".join(doc.get("themes", [])),
        " ".join(doc.get("tropes", [])),
        " ".join(doc.get("relationship_dynamics", [])),
    ]
    return " ".join(p for p in parts if p)


@lru_cache(maxsize=1)
def get_client() -> OpenSearch:
    s = get_settings()
    http_auth = None
    if s.opensearch_username and s.opensearch_password:
        http_auth = (s.opensearch_username, s.opensearch_password)
    return OpenSearch(
        hosts=[s.opensearch_url],
        http_auth=http_auth,
        use_ssl=s.opensearch_url.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
        timeout=30,
    )


def ensure_index(recreate: bool = False) -> None:
    client = get_client()
    index = get_settings().opensearch_index
    exists = client.indices.exists(index=index)
    if exists and recreate:
        client.indices.delete(index=index)
        exists = False
    if not exists:
        client.indices.create(index=index, body=INDEX_MAPPING)
