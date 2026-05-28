from __future__ import annotations

from collections import OrderedDict

from ..embeddings import embed_query
from ..schemas import MatchedPassage, SearchHit, SearchRequest, Work

GROUP_FETCH_MULTIPLIER = 20


def _fetch_size(req: SearchRequest) -> int:
    return req.page * req.size * GROUP_FETCH_MULTIPLIER


def _chunk_filter_clauses(req: SearchRequest) -> list[dict]:
    clauses: list[dict] = []
    f = req.filters
    if f.genres:
        clauses.append({"terms": {"genres": f.genres}})
    for theme in f.themes:
        clauses.append({"term": {"themes": theme}})
    return clauses


def build_chunk_bm25_query(req: SearchRequest) -> dict:
    must: list[dict] = []
    if req.query.strip():
        must.append(
            {
                "multi_match": {
                    "query": req.query,
                    "fields": [
                        "text_chunk^4",
                        "title^2",
                        "creator",
                        "genres^1.5",
                        "themes^1.5",
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

    return {
        "size": _fetch_size(req),
        "query": {
            "bool": {
                "must": must,
                "filter": _chunk_filter_clauses(req),
            }
        },
        "_source": {"excludes": ["combined_text", "embedding"]},
    }


def build_chunk_dense_query(req: SearchRequest) -> dict:
    k = _fetch_size(req)
    if req.query.strip():
        knn_body: dict = {
            "vector": embed_query(req.query),
            "k": k,
        }
        filter_clauses = _chunk_filter_clauses(req)
        if filter_clauses:
            knn_body["filter"] = {"bool": {"filter": filter_clauses}}
        query = {"knn": {"embedding": knn_body}}
    else:
        query = {
            "bool": {
                "must": [{"match_all": {}}],
                "filter": _chunk_filter_clauses(req),
            }
        }
    return {
        "size": k,
        "query": query,
        "_source": {"excludes": ["combined_text", "embedding"]},
    }


def build_chunk_hybrid_queries(req: SearchRequest) -> tuple[dict, dict]:
    fusion_req = req.model_copy(update={"page": 1, "size": req.page * req.size})
    return build_chunk_bm25_query(fusion_req), build_chunk_dense_query(fusion_req)


def _fallback_work_from_chunk(source: dict) -> Work:
    return Work.model_validate(
        {
            "work_id": source["work_id"],
            "title": source.get("title") or "Untitled",
            "creator": source.get("creator") or "Unknown",
            "format": source.get("format") or "novel",
            "summary": source.get("summary") or source.get("text_chunk") or "",
            "genres": source.get("genres", []),
            "themes": source.get("themes", []),
            "tropes": source.get("tropes", []),
            "relationship_dynamics": source.get("relationship_dynamics", []),
            "content_warnings": source.get("content_warnings", ["unknown"]),
            "audience_rating": source.get("audience_rating") or "General",
            "status": source.get("status") or "Complete",
            "length_bucket": source.get("length_bucket") or "medium",
            "language": source.get("language") or "English",
            "source": source.get("source") or "project_gutenberg",
            "book_id": source.get("book_id"),
            "pg_subjects": source.get("pg_subjects", source.get("themes", [])),
            "topics": source.get("topics", source.get("genres", [])),
            "release_date": source.get("release_date"),
        }
    )


def _load_works_by_id(client, works_index: str, work_ids: list[str]) -> dict[str, Work]:
    if not work_ids:
        return {}
    res = client.mget(index=works_index, body={"ids": work_ids})
    works: dict[str, Work] = {}
    for doc in res.get("docs", []):
        if doc.get("found"):
            source = dict(doc["_source"])
            source.pop("combined_text", None)
            source.pop("embedding", None)
            works[doc["_id"]] = Work.model_validate(source)
    return works


def _has_all(values: list[str], selected: list[str]) -> bool:
    return all(value in values for value in selected)


def _has_any(values: list[str], selected: list[str]) -> bool:
    return not selected or any(value in values for value in selected)


def _work_matches_filters(work: Work, req: SearchRequest) -> bool:
    f = req.filters
    if f.formats and work.format not in f.formats:
        return False
    if not _has_any(work.genres, f.genres):
        return False
    if not _has_all(work.tropes, f.tropes):
        return False
    if not _has_all(work.themes, f.themes):
        return False
    if f.statuses and work.status not in f.statuses:
        return False
    if f.length_buckets and work.length_bucket not in f.length_buckets:
        return False
    if f.audience_ratings and work.audience_rating not in f.audience_ratings:
        return False
    if f.languages and work.language not in f.languages:
        return False
    if req.exclude_warnings and any(warning in work.content_warnings for warning in req.exclude_warnings):
        return False
    return True


def group_chunk_hits(
    chunk_hits: list[dict],
    *,
    client,
    works_index: str,
    req: SearchRequest,
    page: int,
    size: int,
) -> tuple[list[SearchHit], int]:
    grouped: OrderedDict[str, dict] = OrderedDict()
    for hit in chunk_hits:
        source = hit["_source"]
        work_id = source["work_id"]
        passage = MatchedPassage(
            chunk_id=source["chunk_id"],
            chunk_index=int(source.get("chunk_index") or 0),
            text_chunk=source.get("text_chunk", ""),
            score=float(hit.get("_score") or 0.0),
        )
        if work_id not in grouped:
            grouped[work_id] = {
                "score": float(hit.get("_score") or 0.0),
                "source": source,
                "passages": [passage],
            }
        elif len(grouped[work_id]["passages"]) < 3:
            grouped[work_id]["passages"].append(passage)

    work_ids = list(grouped)
    works = _load_works_by_id(client, works_index, work_ids)
    filtered_items: list[tuple[str, dict, Work]] = []
    for work_id in work_ids:
        item = grouped[work_id]
        work = works.get(work_id) or _fallback_work_from_chunk(item["source"])
        if _work_matches_filters(work, req):
            filtered_items.append((work_id, item, work))

    offset = (page - 1) * size
    selected_items = filtered_items[offset : offset + size]

    results: list[SearchHit] = []
    for _work_id, item, work in selected_items:
        results.append(
            SearchHit(
                work=work,
                score=item["score"],
                explanation=["Matched by Gutenberg content passage"],
                matched_passages=item["passages"],
            )
        )
    return results, len(filtered_items)
