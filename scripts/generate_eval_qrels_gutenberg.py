"""Generate rule-derived qrels for Gutenberg-adapted StorySeek works.

The Gutenberg query set is subject/topic oriented, because public-domain book
metadata does not include StorySeek's synthetic trope labels.

This is a bootstrap helper. The main checked-in Gutenberg evaluation file,
`data/eval/gutenberg_qrels.csv`, is LLM-assisted pooled qrels and should not be
overwritten by this script unless intentionally requested with `--out`.

Usage:
    python scripts/generate_eval_qrels_gutenberg.py
    python scripts/generate_eval_qrels_gutenberg.py --works data/sample/works_gutenberg.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERIES = REPO_ROOT / "data" / "eval" / "gutenberg_queries.jsonl"
DEFAULT_WORKS = REPO_ROOT / "data" / "sample" / "works_gutenberg.jsonl"
DEFAULT_QRELS = REPO_ROOT / "data" / "eval" / "gutenberg_qrels_rule.csv"


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _norm(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _contains_any(haystack: str, needles: list[str]) -> set[str]:
    return {needle for needle in needles if needle and needle in haystack}


def _grade(query: dict, work: dict) -> int:
    target_topics = [_norm(x) for x in query.get("target_topics", [])]
    target_keywords = [_norm(x) for x in query.get("target_subject_keywords", [])]

    work_topics = {_norm(x) for x in work.get("topics", []) or work.get("genres", [])}
    work_subjects = {_norm(x) for x in work.get("pg_subjects", []) or work.get("themes", [])}
    searchable_text = _norm(
        " ".join(
            [
                work.get("title", ""),
                work.get("summary", ""),
                " ".join(work_topics),
                " ".join(work_subjects),
            ]
        )
    )

    topic_hits = set(target_topics) & work_topics
    subject_hits = _contains_any(" ".join(work_subjects), target_keywords)
    text_hits = _contains_any(searchable_text, target_keywords)

    if topic_hits and subject_hits:
        return 3
    if topic_hits or subject_hits:
        return 2
    if text_hits:
        return 1
    return 0


def write_qrels(queries_path: Path, works_path: Path, qrels_path: Path) -> int:
    queries = _load_jsonl(queries_path)
    works = _load_jsonl(works_path)

    qrels_path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with qrels_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "work_id", "relevance"])
        for query in queries:
            graded: list[tuple[str, int]] = []
            for work in works:
                relevance = _grade(query, work)
                if relevance > 0:
                    graded.append((work["work_id"], relevance))
            graded.sort(key=lambda item: (-item[1], item[0]))
            for work_id, relevance in graded:
                writer.writerow([query["query_id"], work_id, relevance])
                total += 1
            print(f"{query['query_id']}: {len(graded)} judged-relevant docs")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Gutenberg qrels for StorySeek.")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--works", type=Path, default=DEFAULT_WORKS)
    parser.add_argument("--out", type=Path, default=DEFAULT_QRELS)
    args = parser.parse_args()

    if not args.works.exists():
        raise SystemExit(f"Works file not found: {args.works}")
    total = write_qrels(args.queries, args.works, args.out)
    print(f"Wrote {total} judgments to {args.out}")


if __name__ == "__main__":
    main()
