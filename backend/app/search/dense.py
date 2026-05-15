"""Dense retrieval query builder (kNN)."""
from __future__ import annotations

from ..embeddings import embed_query
from ..schemas import SearchRequest


def build_dense_query(req: SearchRequest) -> dict:
    filter_clauses: list[dict] = []
    f = req.filters
    if f.formats:
        filter_clauses.append({"terms": {"format": f.formats}})
    if f.genres:
        filter_clauses.append({"terms": {"genres": f.genres}})
    for trope in f.tropes:
        filter_clauses.append({"term": {"tropes": trope}})
    for theme in f.themes:
        filter_clauses.append({"term": {"themes": theme}})
    if f.statuses:
        filter_clauses.append({"terms": {"status": f.statuses}})
    if f.length_buckets:
        filter_clauses.append({"terms": {"length_bucket": f.length_buckets}})
    if f.audience_ratings:
        filter_clauses.append({"terms": {"audience_rating": f.audience_ratings}})
    if f.languages:
        filter_clauses.append({"terms": {"language": f.languages}})

    must_not: list[dict] = []
    if req.exclude_warnings:
        must_not.append({"terms": {"content_warnings": req.exclude_warnings}})

    k = req.page * req.size
    if req.query.strip():
        vector = embed_query(req.query)
        must = [
            {
                "knn": {
                    "embedding": {
                        "vector": vector,
                        "k": k,
                        "num_candidates": max(100, k * 2),
                    }
                }
            }
        ]
    else:
        must = [{"match_all": {}}]

    return {
        "size": k,
        "query": {
            "bool": {
                "must": must,
                "filter": filter_clauses,
                "must_not": must_not,
            }
        },
        "_source": {"excludes": ["combined_text", "embedding"]},
    }
