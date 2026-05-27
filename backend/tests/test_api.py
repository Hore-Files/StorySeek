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

    def search(self, *, index: str, body: dict) -> dict:
        self.calls.append({"index": index, "body": body})
        return self.responses.pop(0)

    def get(self, *, index: str, id: str) -> dict:
        self.calls.append({"index": index, "id": id, "body": None})
        return self.get_response


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


def test_search_dense_routes_to_dense_builder(monkeypatch):
    fake = FakeClient([_search_response("w_1")])
    monkeypatch.setattr(main, "get_client", lambda: fake)
    monkeypatch.setattr(main, "build_dense_query", lambda req: {"query": {"dense": req.mode}, "size": req.size})
    client = TestClient(main.app)

    resp = client.post("/search", json={"query": "slow burn", "mode": "dense"})

    assert resp.status_code == 200
    assert resp.json()["mode"] == "dense"
    assert fake.calls[0]["body"]["query"] == {"dense": "dense"}


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
