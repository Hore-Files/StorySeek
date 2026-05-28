from __future__ import annotations

import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from opensearchpy.exceptions import NotFoundError, OpenSearchException

from .config import get_settings
from .opensearch_client import EMBEDDING_LOOKUP_SOURCE_EXCLUDES, SEARCH_SOURCE_EXCLUDES, get_client
from .schemas import SearchHit, SearchRequest, SearchResponse, Work
from .search.bm25 import build_bm25_query
from .search.dense import build_dense_query
from .search.explain import explain_hit
from .search.hybrid import build_hybrid_queries, reciprocal_rank_fusion

app = FastAPI(title="StorySeek API", version="0.1.0")
logger = logging.getLogger("storyseek.api")

# Allow React frontend to call this API from the browser (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:8501",  # Streamlit (legacy)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request path=%s method=%s status=%s latency_ms=%.1f",
        request.url.path,
        request.method,
        response.status_code,
        latency_ms,
    )
    return response


@app.get("/health")
def health() -> dict:
    client = get_client()
    try:
        cluster_health = client.cluster.health()
        return {
            "status": "ok",
            "opensearch": cluster_health.get("status", "unknown"),
            "index": get_settings().search_index,
        }
    except OpenSearchException as exc:
        return {"status": "degraded", "error": str(exc)}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    if req.mode == "bm25":
        body = build_bm25_query(req)
    elif req.mode == "dense":
        body = build_dense_query(req)
    else:
        return hybrid_search(req)

    client = get_client()
    res = client.search(index=get_settings().search_index, body=body)
    if req.mode == "bm25":
        total = res["hits"]["total"]["value"]
        raw_hits = res["hits"]["hits"]
    else:
        offset = (req.page - 1) * req.size
        raw_hits = res["hits"]["hits"][offset : offset + req.size]
        total = len(res["hits"]["hits"])
    hits: list[SearchHit] = []
    for h in raw_hits:
        work = Work.model_validate(h["_source"])
        hits.append(
            SearchHit(
                work=work,
                score=float(h.get("_score") or 0.0),
                explanation=explain_hit(work, req),
            )
        )
    response = SearchResponse(
        query=req.query,
        mode=req.mode,
        total=total,
        page=req.page,
        size=req.size,
        hits=hits,
    )
    logger.info(
        "search_complete mode=%s total=%s returned=%s page=%s size=%s",
        req.mode,
        total,
        len(hits),
        req.page,
        req.size,
    )
    return response


def hybrid_search(req: SearchRequest) -> SearchResponse:
    client = get_client()
    index = get_settings().search_index
    bm25_body, dense_body = build_hybrid_queries(req)
    bm25_res = client.search(index=index, body=bm25_body)
    dense_res = client.search(index=index, body=dense_body)
    fused = reciprocal_rank_fusion(
        [
            bm25_res["hits"]["hits"],
            dense_res["hits"]["hits"],
        ]
    )
    offset = (req.page - 1) * req.size
    raw_hits = fused[offset : offset + req.size]

    hits: list[SearchHit] = []
    for h in raw_hits:
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
        total=len(fused),
        page=req.page,
        size=req.size,
        hits=hits,
    )


@app.get("/works/{work_id}", response_model=Work)
def get_work(work_id: str) -> Work:
    client = get_client()
    try:
        res = client.get(
            index=get_settings().search_index,
            id=work_id,
            _source_excludes=SEARCH_SOURCE_EXCLUDES,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"work_id '{work_id}' not found") from exc
    source = res["_source"]
    return Work.model_validate(source)


@app.get("/similar/{work_id}", response_model=SearchResponse)
def similar(work_id: str, size: int = 10) -> SearchResponse:
    client = get_client()
    index = get_settings().search_index
    try:
        source_doc = client.get(
            index=index,
            id=work_id,
            _source_excludes=EMBEDDING_LOOKUP_SOURCE_EXCLUDES,
        )["_source"]
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"work_id '{work_id}' not found") from exc

    embedding = source_doc.get("embedding")
    if embedding:
        try:
            return _dense_similar(client, index, work_id, embedding, size)
        except OpenSearchException:
            logger.exception("dense_similar_failed work_id=%s fallback=more_like_this", work_id)

    return _text_similar(client, index, work_id, size)


def _dense_similar(client, index: str, work_id: str, embedding: list[float], size: int) -> SearchResponse:
    body = {
        "size": size,
        "query": {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": size + 1,
                    "filter": {"bool": {"must_not": [{"ids": {"values": [work_id]}}]}},
                }
            }
        },
        "_source": {"excludes": SEARCH_SOURCE_EXCLUDES},
    }
    res = client.search(index=index, body=body)
    hits = _similar_hits(res, work_id, "Similar by dense embedding over title, summary, and tags")
    return SearchResponse(
        query=f"similar:{work_id}",
        mode="dense",
        total=len(hits),
        page=1,
        size=size,
        hits=hits[:size],
    )


def _text_similar(client, index: str, work_id: str, size: int) -> SearchResponse:
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
        "_source": {"excludes": SEARCH_SOURCE_EXCLUDES},
    }
    res = client.search(index=index, body=body)
    hits = _similar_hits(res, work_id, "Similar by shared title/summary/tag text (more_like_this)")
    return SearchResponse(
        query=f"similar:{work_id}",
        mode="bm25",
        total=len(hits),
        page=1,
        size=size,
        hits=hits[:size],
    )


def _similar_hits(res: dict, work_id: str, explanation: str) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for h in res["hits"]["hits"]:
        if h["_id"] == work_id:
            continue
        work = Work.model_validate(h["_source"])
        hits.append(
            SearchHit(
                work=work,
                score=float(h.get("_score") or 0.0),
                explanation=[explanation],
            )
        )
    return hits
