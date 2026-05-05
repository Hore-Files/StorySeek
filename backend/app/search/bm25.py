from __future__ import annotations

from ..schemas import SearchRequest


def build_bm25_query(req: SearchRequest) -> dict:
    must: list[dict] = []
    if req.query.strip():
        must.append(
            {
                "multi_match": {
                    "query": req.query,
                    "fields": [
                        "title^3",
                        "summary^2",
                        "genres^1.5",
                        "themes^1.5",
                        "tropes^2",
                        "relationship_dynamics",
                        "combined_text",
                    ],
                    "type": "best_fields",
                    "operator": "or",
                    "tie_breaker": 0.2,
                }
            }
        )
    else:
        must.append({"match_all": {}})

    filter_clauses: list[dict] = []
    f = req.filters
    if f.formats:
        filter_clauses.append({"terms": {"format": f.formats}})
    if f.genres:
        filter_clauses.append({"terms": {"genres": f.genres}})
    if f.tropes:
        filter_clauses.append({"terms": {"tropes": f.tropes}})
    if f.themes:
        filter_clauses.append({"terms": {"themes": f.themes}})
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

    body: dict = {
        "from": (req.page - 1) * req.size,
        "size": req.size,
        "query": {
            "bool": {
                "must": must,
                "filter": filter_clauses,
                "must_not": must_not,
            }
        },
        "_source": {"excludes": ["combined_text"]},
    }
    return body
