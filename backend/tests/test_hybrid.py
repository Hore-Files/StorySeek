from __future__ import annotations

from backend.app.schemas import SearchRequest
from backend.app.search.hybrid import build_hybrid_queries, reciprocal_rank_fusion


def _hit(doc_id: str, score: float) -> dict:
    return {"_id": doc_id, "_score": score, "_source": {"work_id": doc_id}}


def test_rrf_merges_duplicates_and_orders_by_fused_rank():
    bm25 = [_hit("w_1", 10.0), _hit("w_2", 9.0), _hit("w_3", 1.0)]
    dense = [_hit("w_2", 0.9), _hit("w_4", 0.8), _hit("w_1", 0.1)]

    fused = reciprocal_rank_fusion([bm25, dense], k=60)

    assert [h["_id"] for h in fused] == ["w_2", "w_1", "w_4", "w_3"]
    assert len(fused) == 4
    assert fused[0]["_source"]["work_id"] == "w_2"


def test_build_hybrid_queries_fetches_enough_for_requested_page(monkeypatch):
    bm25_sizes: list[int] = []
    dense_sizes: list[int] = []

    def fake_bm25(req: SearchRequest) -> dict:
        bm25_sizes.append(req.size)
        return {"size": req.size}

    def fake_dense(req: SearchRequest) -> dict:
        dense_sizes.append(req.size)
        return {"size": req.size}

    monkeypatch.setattr("backend.app.search.hybrid.build_bm25_query", fake_bm25)
    monkeypatch.setattr("backend.app.search.hybrid.build_dense_query", fake_dense)

    build_hybrid_queries(SearchRequest(query="x", page=3, size=10))

    assert bm25_sizes == [30]
    assert dense_sizes == [30]
