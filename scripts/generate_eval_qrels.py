"""Derive a relevance-judgments file (qrels) from queries.jsonl + works.jsonl.

We do not have a hand-labeled gold set for the synthetic corpus, so qrels are
**rule-derived** from the structured metadata that defines each query. The
rules are explicit and documented (see docs/evaluation.md) so the eval story
remains reproducible. When a real dataset replaces synthetic, hand-labeling
replaces this generator.

Relevance scale (matches docs/evaluation.md):

    3 — all target tropes AND all target themes AND all target genres match,
        and no excluded warning is present.
    2 — at least one target trope AND one target theme match (if both kinds
        are specified), or all targets of a single kind match; no excluded
        warning.
    1 — any single target overlap (trope, theme, or genre), no excluded
        warning.
    0 — no overlap, or the work contains a query-excluded content warning.

Only rows with relevance >= 1 are written; unjudged docs are treated as 0 by
standard IR convention.

Usage:
    python scripts/generate_eval_qrels.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERIES = REPO_ROOT / "data" / "eval" / "queries.jsonl"
WORKS = REPO_ROOT / "data" / "sample" / "works.jsonl"
QRELS = REPO_ROOT / "data" / "eval" / "qrels.csv"


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _grade(query: dict, work: dict) -> int:
    excluded = set(query.get("exclude_warnings", []))
    if excluded & set(work.get("content_warnings", [])):
        return 0

    target_tropes = set(query.get("target_tropes", []))
    target_themes = set(query.get("target_themes", []))
    target_genres = set(query.get("target_genres", []))

    work_tropes = set(work.get("tropes", []))
    work_themes = set(work.get("themes", []))
    work_genres = set(work.get("genres", []))

    trope_hits = target_tropes & work_tropes
    theme_hits = target_themes & work_themes
    genre_hits = target_genres & work_genres

    full_trope = (not target_tropes) or trope_hits == target_tropes
    full_theme = (not target_themes) or theme_hits == target_themes
    full_genre = (not target_genres) or genre_hits == target_genres
    if full_trope and full_theme and full_genre and (target_tropes or target_themes or target_genres):
        return 3

    kinds_specified = [bool(target_tropes), bool(target_themes), bool(target_genres)]
    n_specified = sum(kinds_specified)
    if n_specified >= 2:
        # Partial across kinds: at least one hit in each specified kind.
        per_kind_ok = (
            (not target_tropes or trope_hits)
            and (not target_themes or theme_hits)
            and (not target_genres or genre_hits)
        )
        if per_kind_ok:
            return 2
    # Single-kind full match also rates a 2.
    if n_specified == 1 and (full_trope and full_theme and full_genre):
        return 2

    if trope_hits or theme_hits or genre_hits:
        return 1
    return 0


def main() -> None:
    queries = _load_jsonl(QUERIES)
    works = _load_jsonl(WORKS)

    QRELS.parent.mkdir(parents=True, exist_ok=True)
    with QRELS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "work_id", "relevance"])
        total = 0
        for q in queries:
            graded = []
            for w in works:
                rel = _grade(q, w)
                if rel > 0:
                    graded.append((w["work_id"], rel))
            graded.sort(key=lambda x: (-x[1], x[0]))
            for wid, rel in graded:
                writer.writerow([q["query_id"], wid, rel])
                total += 1
            print(f"{q['query_id']}: {len(graded)} judged-relevant docs")
    print(f"Wrote {total} judgments to {QRELS}")


if __name__ == "__main__":
    main()
