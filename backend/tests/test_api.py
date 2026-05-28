from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import main


def _source(work_id: str = "w_1") -> dict:
    return {
        "work_id": work_id,
        "title": f"Story {work_id}",
        "creator": "Author",
        "format": "novel",
        "summary": "A slow burn story.",
        "genres": ["romance"],
        "themes": ["healing"],
        "tropes": ["slow burn"],
        "relationship_dynamics": ["rivals"],
        "content_warnings": ["none"],
        "audience_rating": "Teen",
        "status": "Complete",
        "length_bucket": "medium",
        "language": "English",
        "source": "synthetic",
    }


class FakeClient:
    def __init__(self, responses: list[dict], get_response: dict | None = None) -> None:
        self.responses = responses
        self.get_response = get_response or {"_source": _source("w_1") | {"embedding": [0.1] * 384}}
        self.calls: list[dict] = []
        self.mget_response: dict = {"docs": []}

    def search(self, *, index: str, body: dict) -> dict:
        self.calls.append({"index": index, "body": body})
        return self.responses.pop(0)

    def get(self, *, index: str, id: str, **kwargs) -> dict:
        self.calls.append({"index": index, "id": id, "body": None, **kwargs})
        return self.get_response

    def mget(self, *, index: str, body: dict) -> dict:
        self.calls.append({"index": index, "body": {"mget": body}})
        return self.mget_response


def _search_response(*ids: str) -> dict:
    return {
        "hits": {
            "total": {"value": len(ids)},
            "hits": [
                {"_id": work_id, "_score": float(i + 1), "_source": _source(work_id)}
                for i, work_id in enumerate(ids)
            ],
        }
    }


def _facet_response() -> dict:
    buckets = {
        "formats": ["novel", "short_story"],
        "genres": ["adventure", "mystery"],
        "tropes": ["found family", "slow burn"],
        "themes": ["friendship", "redemption"],
        "statuses": ["Complete"],
        "length_buckets": ["long", "medium", "short"],
        "audience_ratings": ["General", "Teen"],
        "languages": ["English"],
        "content_warnings": ["graphic violence", "major character death", "none"],
    }
    return {
        "aggregations": {
            name: {"buckets": [{"key": key, "doc_count": 1} for key in keys]}
            for name, keys in buckets.items()
        }
    }


def _source_with(work_id: str, **overrides) -> dict:
    source = _source(work_id)
    source.update(overrides)
    return source


def _chunk_response(*chunks: tuple[str, str, int, str]) -> dict:
    return {
        "hits": {
            "total": {"value": len(chunks)},
            "hits": [
                {
                    "_id": chunk_id,
                    "_score": float(i + 1),
                    "_source": {
                        "chunk_id": chunk_id,
                        "work_id": work_id,
                        "book_id": work_id.replace("pg_", ""),
                        "chunk_index": chunk_index,
                        "title": f"Book {work_id}",
                        "creator": "Author",
                        "genres": ["detective and mystery stories"],
                        "themes": ["gardens -- fiction"],
                        "text_chunk": text,
                        "source": "project_gutenberg",
                    },
                }
                for i, (chunk_id, work_id, chunk_index, text) in enumerate(chunks)
            ],
        }
    }


def test_search_dense_routes_to_dense_builder(monkeypatch):
    fake = FakeClient([_search_response("w_1")])
    monkeypatch.setattr(main, "get_client", lambda: fake)
    monkeypatch.setattr(main, "build_dense_query", lambda req: {"query": {"dense": req.mode}, "size": req.size})
    client = TestClient(main.app)

    resp = client.post("/search", json={"query": "slow burn", "mode": "dense"})

    assert resp.status_code == 200
    assert resp.json()["mode"] == "dense"
    assert fake.calls[0]["body"]["query"] == {"dense": "dense"}


def test_facets_returns_index_values_and_hides_none_warning(monkeypatch):
    fake = FakeClient([_facet_response()])
    monkeypatch.setattr(main, "get_client", lambda: fake)
    client = TestClient(main.app)

    resp = client.get("/facets")

    assert resp.status_code == 200
    body = resp.json()
    assert body["formats"] == ["novel", "short_story"]
    assert body["genres"] == ["adventure", "mystery"]
    assert body["content_warnings"] == ["graphic violence", "major character death"]
    assert fake.calls[0]["body"]["size"] == 0
    assert set(fake.calls[0]["body"]["aggs"]) >= {
        "formats",
        "genres",
        "tropes",
        "themes",
        "statuses",
        "length_buckets",
        "audience_ratings",
        "languages",
        "content_warnings",
    }


def test_search_hybrid_fuses_two_result_sets(monkeypatch):
    fake = FakeClient([_search_response("w_1", "w_2"), _search_response("w_2", "w_3")])
    monkeypatch.setattr(main, "get_client", lambda: fake)
    monkeypatch.setattr(main, "build_hybrid_queries", lambda req: ({"name": "bm25"}, {"name": "dense"}))
    client = TestClient(main.app)

    resp = client.post("/search", json={"query": "slow burn", "mode": "hybrid", "size": 3})

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "hybrid"
    assert [h["work"]["work_id"] for h in body["hits"]] == ["w_2", "w_1", "w_3"]
    assert [call["body"] for call in fake.calls] == [{"name": "bm25"}, {"name": "dense"}]


def test_similar_uses_dense_embedding_and_excludes_source_work(monkeypatch):
    fake = FakeClient([_search_response("w_1", "w_2")])
    monkeypatch.setattr(main, "get_client", lambda: fake)
    client = TestClient(main.app)

    resp = client.get("/similar/w_1?size=2")

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "dense"
    assert body["total"] == 1
    assert [h["work"]["work_id"] for h in body["hits"]] == ["w_2"]
    assert fake.calls[1]["body"]["query"]["knn"]["embedding"]["k"] == 3


def test_similar_falls_back_to_text_when_embedding_missing(monkeypatch):
    fake = FakeClient([_search_response("w_1", "w_2")], get_response={"_source": _source("w_1")})
    monkeypatch.setattr(main, "get_client", lambda: fake)
    client = TestClient(main.app)

    resp = client.get("/similar/w_1?size=2")

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "bm25"
    assert [h["work"]["work_id"] for h in body["hits"]] == ["w_2"]
    assert "more_like_this" in fake.calls[1]["body"]["query"]


def test_search_content_groups_chunks_by_work_and_returns_passages(monkeypatch):
    fake = FakeClient(
        [
            _chunk_response(
                ("pg_1_c000001", "pg_1", 1, "The detective found blood near the garden gate."),
                ("pg_1_c000002", "pg_1", 2, "The clue led back to the old house."),
                ("pg_2_c000001", "pg_2", 1, "Another mystery began at midnight."),
            )
        ]
    )
    fake.mget_response = {
        "docs": [
            {"_id": "pg_1", "found": True, "_source": _source("pg_1")},
            {"_id": "pg_2", "found": True, "_source": _source("pg_2")},
        ]
    }
    monkeypatch.setattr(main, "get_client", lambda: fake)
    client = TestClient(main.app)

    resp = client.post("/search-content", json={"query": "blood near garden gate", "mode": "bm25", "size": 5})

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert [h["work"]["work_id"] for h in body["hits"]] == ["pg_1", "pg_2"]
    assert len(body["hits"][0]["matched_passages"]) == 2
    assert body["hits"][0]["matched_passages"][0]["chunk_id"] == "pg_1_c000001"


def test_search_content_applies_work_level_filters_after_grouping(monkeypatch):
    fake = FakeClient(
        [
            _chunk_response(
                ("pg_1_c000001", "pg_1", 1, "The detective found blood near the garden gate."),
                ("pg_2_c000001", "pg_2", 1, "Another mystery began at midnight."),
            )
        ]
    )
    fake.mget_response = {
        "docs": [
            {
                "_id": "pg_1",
                "found": True,
                "_source": _source_with("pg_1", format="novel", audience_rating="General"),
            },
            {
                "_id": "pg_2",
                "found": True,
                "_source": _source_with("pg_2", format="short_story", audience_rating="Teen"),
            },
        ]
    }
    monkeypatch.setattr(main, "get_client", lambda: fake)
    client = TestClient(main.app)

    resp = client.post(
        "/search-content",
        json={
            "query": "mystery",
            "mode": "bm25",
            "filters": {
                "formats": ["short_story"],
                "audience_ratings": ["Teen"],
            },
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert [h["work"]["work_id"] for h in body["hits"]] == ["pg_2"]
