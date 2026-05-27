"""Hybrid retrieval helpers using Reciprocal Rank Fusion."""
from __future__ import annotations

from collections.abc import Iterable

from ..schemas import SearchRequest
from .bm25 import build_bm25_query
from .dense import build_dense_query

RRF_K = 60


def build_hybrid_queries(req: SearchRequest) -> tuple[dict, dict]:
    """Build oversized BM25 and dense queries for rank fusion."""
    fusion_req = req.model_copy(update={"page": 1, "size": req.page * req.size})
    return build_bm25_query(fusion_req), build_dense_query(fusion_req)


def reciprocal_rank_fusion(
    ranked_lists: Iterable[list[dict]],
    *,
    k: int = RRF_K,
) -> list[dict]:
    """Fuse OpenSearch hits while preserving each document's best source payload."""
    scores: dict[str, float] = {}
    best_hits: dict[str, dict] = {}
    best_raw_scores: dict[str, float] = {}

    for hits in ranked_lists:
        for rank, hit in enumerate(hits, start=1):
            doc_id = hit["_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            raw_score = float(hit.get("_score") or 0.0)
            if doc_id not in best_hits or raw_score > best_raw_scores[doc_id]:
                best_hits[doc_id] = hit
                best_raw_scores[doc_id] = raw_score

    fused: list[dict] = []
    for doc_id, fused_score in scores.items():
        hit = dict(best_hits[doc_id])
        hit["_score"] = fused_score
        fused.append(hit)

    return sorted(fused, key=lambda h: (-float(h.get("_score") or 0.0), h["_id"]))
