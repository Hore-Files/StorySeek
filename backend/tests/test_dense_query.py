from __future__ import annotations

from backend.app.schemas import SearchFilters, SearchRequest
from backend.app.search import dense


def test_dense_query_uses_knn_and_filters(monkeypatch):
    monkeypatch.setattr(dense, "embed_query", lambda text: [0.1] * 384)
    body = dense.build_dense_query(
        SearchRequest(
            query="slow burn found family",
            filters=SearchFilters(
                formats=["novel"],
                tropes=["slow burn", "found family"],
                themes=["healing"],
            ),
            exclude_warnings=["major character death"],
            page=2,
            size=5,
        )
    )

    knn = body["query"]["knn"]["embedding"]
    assert knn["vector"] == [0.1] * 384
    assert knn["k"] == 10
    knn_filter = knn["filter"]["bool"]
    assert {"terms": {"format": ["novel"]}} in knn_filter["filter"]
    assert {"term": {"tropes": "slow burn"}} in knn_filter["filter"]
    assert {"term": {"tropes": "found family"}} in knn_filter["filter"]
    assert {"term": {"themes": "healing"}} in knn_filter["filter"]
    assert knn_filter["must_not"] == [{"terms": {"content_warnings": ["major character death"]}}]
    assert body["_source"]["excludes"] == ["combined_text", "embedding"]


def test_dense_empty_query_uses_match_all():
    body = dense.build_dense_query(SearchRequest(query=""))
    assert body["query"]["bool"]["must"] == [{"match_all": {}}]
