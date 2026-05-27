from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache

from opensearchpy import OpenSearch

from .config import get_settings

# Index mapping. `combined_text` feeds BM25 and explanation support; `embedding`
# feeds dense kNN and hybrid retrieval.
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


def versioned_index_name(alias: str | None = None) -> str:
    base = alias or get_settings().search_index
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"{base}_v{stamp}"


def ensure_index(index: str | None = None, recreate: bool = False) -> str:
    client = get_client()
    index = index or get_settings().search_index
    exists = client.indices.exists(index=index)
    if exists and recreate:
        client.indices.delete(index=index)
        exists = False
    if not exists:
        client.indices.create(index=index, body=INDEX_MAPPING)
    return index


def alias_targets(alias: str | None = None) -> list[str]:
    client = get_client()
    alias = alias or get_settings().search_index
    try:
        aliases = client.indices.get_alias(name=alias)
    except Exception:
        return []
    return sorted(aliases.keys())


def index_exists(name: str) -> bool:
    return bool(get_client().indices.exists(index=name))


def delete_index(name: str) -> None:
    get_client().indices.delete(index=name)


def swap_alias(alias: str, new_index: str) -> None:
    client = get_client()
    actions = [{"remove": {"index": old, "alias": alias}} for old in alias_targets(alias)]
    actions.append({"add": {"index": new_index, "alias": alias}})
    client.indices.update_aliases(body={"actions": actions})
