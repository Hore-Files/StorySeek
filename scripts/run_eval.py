"""Run retrieval evaluation against a running StorySeek backend.

Computes nDCG@10, MRR@10, and Recall@20 for each query using judgments
from a qrels CSV file.

Prereqs:
    - OpenSearch is running and the needed index is built.
    - The FastAPI backend is reachable at BACKEND_URL (default http://localhost:8000).

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --backend http://localhost:8000 --k-recall 20
    python scripts/run_eval.py --modes bm25 dense hybrid
    python scripts/run_eval.py --endpoint /search-content --queries data/eval/gutenberg_queries.jsonl --qrels data/eval/gutenberg_qrels.csv
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
DEFAULT_QUERIES = REPO_ROOT / "data" / "eval" / "queries.jsonl"
DEFAULT_QRELS = REPO_ROOT / "data" / "eval" / "qrels.csv"
DEFAULT_OUT = REPO_ROOT / "reports" / "metrics.json"
DEFAULT_COMPARISON_OUT = REPO_ROOT / "reports" / "comparison.md"
DEFAULT_MODES = ["bm25", "dense", "hybrid"]


def _load_queries(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_qrels(path: Path) -> dict[str, dict[str, int]]:
    rels: dict[str, dict[str, int]] = {}
    if not path.exists():
        return rels
    with path.open("r", encoding="utf-8", newline="") as f:
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


def run_query(backend: str, endpoint: str, query: dict, size: int, mode: str) -> list[str]:
    payload = {
        "query": query["query"],
        "mode": mode,
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
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    resp = requests.post(f"{backend.rstrip('/')}{endpoint}", json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return [h["work"]["work_id"] for h in body["hits"]]


def _mean(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def _qrels_note(args: argparse.Namespace) -> str:
    if "gutenberg" in args.qrels.name.lower():
        return "- Current qrels are LLM-assisted pooled judgments over Project Gutenberg candidates."
    return "- Current qrels are rule-derived from metadata, so dense semantic matches can be under-credited."


def _write_comparison(overall: list[dict], per_mode: dict[str, list[dict]], args: argparse.Namespace) -> None:
    lines = [
        "# StorySeek Retrieval Comparison",
        "",
        "This report compares retrieval modes on the same query set and qrels.",
        "",
        f"- Queries: `{args.queries.as_posix()}`",
        f"- Qrels: `{args.qrels.as_posix()}`",
        f"- Endpoint: `{args.endpoint}`",
        "",
        "| Mode | mean nDCG@{} | mean MRR@{} | mean Recall@{} | Queries |".format(
            args.k_ndcg,
            args.k_mrr,
            args.k_recall,
        ),
        "|---|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(
            "| {method} | {ndcg:.4f} | {mrr:.4f} | {recall:.4f} | {n_queries} |".format(
                method=row["method"],
                ndcg=row[f"mean_nDCG@{args.k_ndcg}"],
                mrr=row[f"mean_MRR@{args.k_mrr}"],
                recall=row[f"mean_Recall@{args.k_recall}"],
                n_queries=row["n_queries"],
            )
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- BM25 is the lexical baseline with field boosting and metadata filters.",
            "- Dense uses sentence-transformer embeddings and OpenSearch kNN search.",
            "- Hybrid uses Reciprocal Rank Fusion over BM25 and Dense rankings.",
            "- `/search` evaluates work-level retrieval; `/search-content` evaluates passage/chunk retrieval grouped back to works.",
            _qrels_note(args),
            "",
            "## Per-query Results",
            "",
        ]
    )
    for mode, rows in per_mode.items():
        lines.extend(
            [
                f"### {mode}",
                "",
                "| Query ID | nDCG@{} | MRR@{} | Recall@{} | Query |".format(
                    args.k_ndcg,
                    args.k_mrr,
                    args.k_recall,
                ),
                "|---|---:|---:|---:|---|",
            ]
        )
        for row in rows:
            lines.append(
                "| {query_id} | {ndcg:.4f} | {mrr:.4f} | {recall:.4f} | {query} |".format(
                    query_id=row["query_id"],
                    ndcg=row[f"nDCG@{args.k_ndcg}"],
                    mrr=row[f"MRR@{args.k_mrr}"],
                    recall=row[f"Recall@{args.k_recall}"],
                    query=row["query"].replace("|", "\\|"),
                )
            )
        lines.append("")

    args.comparison_out.parent.mkdir(parents=True, exist_ok=True)
    args.comparison_out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run StorySeek retrieval eval.")
    parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument(
        "--endpoint",
        default="/search",
        choices=["/search", "/search-content", "search", "search-content"],
        help="Backend search endpoint to evaluate.",
    )
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES, help="Path to queries JSONL file.")
    parser.add_argument("--qrels", type=Path, default=DEFAULT_QRELS, help="Path to qrels CSV file.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Path for metrics JSON output.")
    parser.add_argument(
        "--comparison-out",
        type=Path,
        default=DEFAULT_COMPARISON_OUT,
        help="Path for comparison Markdown output.",
    )
    parser.add_argument("--k-ndcg", type=int, default=10)
    parser.add_argument("--k-mrr", type=int, default=10)
    parser.add_argument("--k-recall", type=int, default=20)
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES, choices=DEFAULT_MODES)
    args = parser.parse_args()
    args.endpoint = args.endpoint if args.endpoint.startswith("/") else f"/{args.endpoint}"

    queries = _load_queries(args.queries)
    qrels = _load_qrels(args.qrels)

    all_overall: list[dict] = []
    per_mode: dict[str, list[dict]] = {}

    for mode in args.modes:
        print(f"\nMode: {mode}")
        per_query: list[dict] = []
        for q in queries:
            qid = q["query_id"]
            try:
                retrieved = run_query(
                    args.backend,
                    args.endpoint,
                    q,
                    size=max(args.k_recall, args.k_ndcg),
                    mode=mode,
                )
            except requests.RequestException as exc:
                print(f"[{mode}:{qid}] backend error: {exc}", file=sys.stderr)
                sys.exit(1)
            qrel = qrels.get(qid, {})
            ndcg = ndcg_at_k(retrieved, qrel, args.k_ndcg)
            mrr = mrr_at_k(retrieved, qrel, args.k_mrr)
            rec = recall_at_k(retrieved, qrel, args.k_recall)
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

        overall = {
            "method": mode,
            f"mean_nDCG@{args.k_ndcg}": round(_mean(per_query, f"nDCG@{args.k_ndcg}"), 4),
            f"mean_MRR@{args.k_mrr}": round(_mean(per_query, f"MRR@{args.k_mrr}"), 4),
            f"mean_Recall@{args.k_recall}": round(_mean(per_query, f"Recall@{args.k_recall}"), 4),
            "n_queries": len(queries),
        }
        all_overall.append(overall)
        per_mode[mode] = per_query

    print("\nOverall:")
    for row in all_overall:
        print(
            f"  {row['method']}: "
            f"mean_nDCG@{args.k_ndcg}={row[f'mean_nDCG@{args.k_ndcg}']:.4f}, "
            f"mean_MRR@{args.k_mrr}={row[f'mean_MRR@{args.k_mrr}']:.4f}, "
            f"mean_Recall@{args.k_recall}={row[f'mean_Recall@{args.k_recall}']:.4f}"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "backend": args.backend,
                "endpoint": args.endpoint,
                "queries": args.queries.as_posix(),
                "qrels": args.qrels.as_posix(),
                "overall": all_overall,
                "per_mode": per_mode,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_comparison(all_overall, per_mode, args)
    print(f"\nWrote {args.out}")
    print(f"Wrote {args.comparison_out}")


if __name__ == "__main__":
    main()
