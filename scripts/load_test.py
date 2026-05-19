"""Lightweight concurrent load test for the StorySeek API.

Prereqs:
    - OpenSearch is running and indexed.
    - FastAPI backend is reachable at BACKEND_URL (default http://localhost:8000).

Usage:
    python scripts/load_test.py
    python scripts/load_test.py --backend http://localhost:8000 --modes bm25 hybrid
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "reports" / "load_test_results.md"
QUERIES = [
    "slow burn rivals to lovers with found family",
    "dark academia mystery with political intrigue",
    "healing fantasy with hurt comfort and no major character death",
    "forbidden magic academy setting",
    "revenge story with villain redemption",
]


def _payload(query: str, mode: str) -> dict:
    return {
        "query": query,
        "mode": mode,
        "page": 1,
        "size": 10,
        "exclude_warnings": ["major character death"],
        "filters": {
            "formats": [],
            "genres": [],
            "tropes": [],
            "themes": [],
            "statuses": [],
            "length_buckets": [],
            "audience_ratings": [],
            "languages": [],
        },
    }


async def _one_request(client: httpx.AsyncClient, query: str, mode: str) -> tuple[float, bool]:
    start = time.perf_counter()
    try:
        resp = await client.post("/search", json=_payload(query, mode))
        ok = resp.status_code == 200
    except httpx.HTTPError:
        ok = False
    return (time.perf_counter() - start) * 1000, ok


async def _run_batch(backend: str, mode: str, concurrency: int, requests_per_user: int) -> dict:
    timeout = httpx.Timeout(60.0)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(base_url=backend, timeout=timeout, limits=limits) as client:
        tasks = [
            _one_request(client, QUERIES[i % len(QUERIES)], mode)
            for i in range(concurrency * requests_per_user)
        ]
        results = await asyncio.gather(*tasks)

    latencies = [lat for lat, _ in results]
    ok_count = sum(1 for _, ok in results if ok)
    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)
    return {
        "mode": mode,
        "concurrency": concurrency,
        "requests": len(results),
        "success_rate": ok_count / len(results),
        "p50_ms": statistics.median(sorted_latencies),
        "p95_ms": sorted_latencies[p95_index],
        "max_ms": max(sorted_latencies),
    }


def _write_report(rows: list[dict]) -> None:
    lines = [
        "# StorySeek Load Test Results",
        "",
        "Lightweight local load test against `POST /search`.",
        "",
        "| Mode | Concurrency | Requests | Success rate | p50 ms | p95 ms | max ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {mode} | {concurrency} | {requests} | {success:.1%} | {p50:.1f} | {p95:.1f} | {max_ms:.1f} |".format(
                mode=row["mode"],
                concurrency=row["concurrency"],
                requests=row["requests"],
                success=row["success_rate"],
                p50=row["p50_ms"],
                p95=row["p95_ms"],
                max_ms=row["max_ms"],
            )
        )
    lines.extend(
        [
            "",
            "## Method",
            "",
            "- Each request uses the same API path as the UI.",
            "- Queries include natural-language trope/theme searches and content-warning exclusion.",
            "- Results are intended as local prototype evidence, not production capacity guarantees.",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")


async def amain() -> None:
    parser = argparse.ArgumentParser(description="Run StorySeek API load test.")
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--modes", nargs="+", default=["bm25", "hybrid"], choices=["bm25", "dense", "hybrid"])
    parser.add_argument("--concurrency", nargs="+", type=int, default=[10, 50, 100])
    parser.add_argument("--requests-per-user", type=int, default=3)
    args = parser.parse_args()

    rows: list[dict] = []
    for mode in args.modes:
        for concurrency in args.concurrency:
            row = await _run_batch(args.backend, mode, concurrency, args.requests_per_user)
            rows.append(row)
            print(json.dumps(row))
    _write_report(rows)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    asyncio.run(amain())
