from __future__ import annotations

from fastapi import FastAPI, HTTPException
from opensearchpy.exceptions import NotFoundError, OpenSearchException

from .config import get_settings
from .opensearch_client import get_client
from .schemas import SearchHit, SearchRequest, SearchResponse, Work
from .search.bm25 import build_bm25_query
from .search.explain import explain_hit

app = FastAPI(title="StorySeek API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    client = get_client()
    try:
        cluster_health = client.cluster.health()
        return {
            "status": "ok",
            "opensearch": cluster_health.get("status", "unknown"),
            "index": get_settings().opensearch_index,
        }
    except OpenSearchException as exc:
        return {"status": "degraded", "error": str(exc)}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    if req.mode != "bm25":
        raise HTTPException(
            status_code=400,
            detail=f"Mode '{req.mode}' not implemented yet. Use 'bm25'.",
        )
    body = build_bm25_query(req)
    client = get_client()
    res = client.search(index=get_settings().opensearch_index, body=body)
    total = res["hits"]["total"]["value"]
    hits: list[SearchHit] = []
    for h in res["hits"]["hits"]:
        work = Work.model_validate(h["_source"])
        hits.append(
            SearchHit(
                work=work,
                score=float(h.get("_score") or 0.0),
                explanation=explain_hit(work, req),
            )
        )
    return SearchResponse(
        query=req.query,
        mode=req.mode,
        total=total,
        page=req.page,
        size=req.size,
        hits=hits,
    )


@app.get("/works/{work_id}", response_model=Work)
def get_work(work_id: str) -> Work:
    client = get_client()
    try:
        res = client.get(index=get_settings().opensearch_index, id=work_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"work_id '{work_id}' not found") from exc
    source = res["_source"]
    source.pop("combined_text", None)
    return Work.model_validate(source)


@app.get("/similar/{work_id}", response_model=SearchResponse)
def similar(work_id: str, size: int = 10) -> SearchResponse:
    """More-like-this placeholder (will be upgraded to vector kNN once dense lands)."""
    client = get_client()
    index = get_settings().opensearch_index
    body = {
        "size": size,
        "query": {
            "more_like_this": {
                "fields": ["combined_text", "title", "summary"],
                "like": [{"_index": index, "_id": work_id}],
                "min_term_freq": 1,
                "max_query_terms": 25,
                "min_doc_freq": 1,
            }
        },
        "_source": {"excludes": ["combined_text"]},
    }
    try:
        res = client.search(index=index, body=body)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"work_id '{work_id}' not found") from exc

    hits: list[SearchHit] = []
    for h in res["hits"]["hits"]:
        if h["_id"] == work_id:
            continue
        work = Work.model_validate(h["_source"])
        hits.append(
            SearchHit(
                work=work,
                score=float(h.get("_score") or 0.0),
                explanation=["Similar by shared title/summary/tag text (more_like_this)"],
            )
        )
    return SearchResponse(
        query=f"similar:{work_id}",
        mode="bm25",
        total=len(hits),
        page=1,
        size=size,
        hits=hits,
    )
