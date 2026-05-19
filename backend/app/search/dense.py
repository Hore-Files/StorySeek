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
        knn_body: dict = {
            "vector": vector,
            "k": k,
        }
        if filter_clauses or must_not:
            knn_body["filter"] = {
                "bool": {
                    "filter": filter_clauses,
                    "must_not": must_not,
                }
            }
        query = {"knn": {"embedding": knn_body}}
    else:
        query = {
            "bool": {
                "must": [{"match_all": {}}],
                "filter": filter_clauses,
                "must_not": must_not,
            }
        }

    return {
        "size": k,
        "query": query,
        "_source": {"excludes": ["combined_text", "embedding"]},
    }
