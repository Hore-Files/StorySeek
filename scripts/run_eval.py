"""Run retrieval evaluation against a running StorySeek backend.

Computes nDCG@10, MRR@10, and Recall@20 for each query in
data/eval/queries.jsonl using judgments from data/eval/qrels.csv.

Prereqs:
    - OpenSearch is running and the index is built (scripts/build_index.py).
    - The FastAPI backend is reachable at BACKEND_URL (default http://localhost:8000).

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --backend http://localhost:8000 --k-recall 20
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERIES = REPO_ROOT / "data" / "eval" / "queries.jsonl"
QRELS = REPO_ROOT / "data" / "eval" / "qrels.csv"
OUT = REPO_ROOT / "reports" / "metrics.json"


def _load_queries() -> list[dict]:
    return [json.loads(line) for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_qrels() -> dict[str, dict[str, int]]:
    rels: dict[str, dict[str, int]] = {}
    with QRELS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rels.setdefault(row["query_id"], {})[row["work_id"]] = int(row["relevance"])
    return rels


def _dcg(gains: list[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(retrieved_ids: list[str], qrel: dict[str, int], k: int) -> float:
    gains = [qrel.get(d, 0) for d in retrieved_ids[:k]]
    ideal = sorted(qrel.values(), reverse=True)[:k]
    idcg = _dcg(ideal)
    if idcg == 0:
        return 0.0
    return _dcg(gains) / idcg


def mrr_at_k(retrieved_ids: list[str], qrel: dict[str, int], k: int) -> float:
    for i, d in enumerate(retrieved_ids[:k], start=1):
        if qrel.get(d, 0) >= 1:
            return 1.0 / i
    return 0.0


def recall_at_k(retrieved_ids: list[str], qrel: dict[str, int], k: int) -> float:
    relevant = {d for d, r in qrel.items() if r >= 1}
    if not relevant:
        return 0.0
    hit = sum(1 for d in retrieved_ids[:k] if d in relevant)
    return hit / len(relevant)


def run_query(backend: str, query: dict, size: int) -> list[str]:
    payload = {
        "query": query["query"],
        "mode": "bm25",
        "page": 1,
        "size": size,
        "exclude_warnings": query.get("exclude_warnings", []),
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
    resp = requests.post(f"{backend}/search", json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return [h["work"]["work_id"] for h in body["hits"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run StorySeek retrieval eval.")
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--k-ndcg", type=int, default=10)
    parser.add_argument("--k-mrr", type=int, default=10)
    parser.add_argument("--k-recall", type=int, default=20)
    args = parser.parse_args()

    queries = _load_queries()
    qrels = _load_qrels()

    per_query: list[dict] = []
    sums = {"ndcg": 0.0, "mrr": 0.0, "recall": 0.0}

    for q in queries:
        qid = q["query_id"]
        try:
            retrieved = run_query(args.backend, q, size=max(args.k_recall, args.k_ndcg))
        except requests.RequestException as exc:
            print(f"[{qid}] backend error: {exc}", file=sys.stderr)
            sys.exit(1)
        qrel = qrels.get(qid, {})
        ndcg = ndcg_at_k(retrieved, qrel, args.k_ndcg)
        mrr = mrr_at_k(retrieved, qrel, args.k_mrr)
        rec = recall_at_k(retrieved, qrel, args.k_recall)
        sums["ndcg"] += ndcg
        sums["mrr"] += mrr
        sums["recall"] += rec
        per_query.append(
            {
                "query_id": qid,
                "query": q["query"],
                "retrieved": len(retrieved),
                f"nDCG@{args.k_ndcg}": round(ndcg, 4),
                f"MRR@{args.k_mrr}": round(mrr, 4),
                f"Recall@{args.k_recall}": round(rec, 4),
            }
        )
        print(
            f"{qid:>6} | nDCG@{args.k_ndcg}={ndcg:.4f}  "
            f"MRR@{args.k_mrr}={mrr:.4f}  Recall@{args.k_recall}={rec:.4f}  "
            f"({q['query'][:60]})"
        )

    n = len(queries)
    overall = {
        "method": "bm25",
        f"mean_nDCG@{args.k_ndcg}": round(sums["ndcg"] / n, 4),
        f"mean_MRR@{args.k_mrr}": round(sums["mrr"] / n, 4),
        f"mean_Recall@{args.k_recall}": round(sums["recall"] / n, 4),
        "n_queries": n,
    }
    print()
    print("Overall (BM25):")
    for k, v in overall.items():
        if k in ("method", "n_queries"):
            continue
        print(f"  {k}: {v}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"overall": overall, "per_query": per_query}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
