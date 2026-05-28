"""Convert Project Gutenberg fiction data into the StorySeek work schema.

The adapter keeps the backend contract stable: one Gutenberg book becomes one
StorySeek-compatible work in JSONL form.

Usage:
    python scripts/convert_gutenberg_to_storyseek.py --limit 20
    python scripts/convert_gutenberg_to_storyseek.py --out data/sample/works_gutenberg.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "sample" / "works_gutenberg.jsonl"
DATASET_NAME = "Despina/project_gutenberg"
DATASET_CONFIG = "fiction_books"
DATASET_SPLIT = "train"

MAX_TAGS = 12
SUMMARY_CHARS = 900
BOILERPLATE_PATTERNS = [
    r"project gutenberg",
    r"this ebook is for the use of anyone",
    r"gutenberg\.org",
    r"project gutenberg license",
    r"start of (the|this) project gutenberg",
    r"end of (the|this) project gutenberg",
    r"produced by",
    r"distributed proofreading",
    r"release date:",
    r"language:",
    r"credits:",
]


def clean_text(text: str | None) -> str:
    """Normalize whitespace while preserving the original prose."""
    return re.sub(r"\s+", " ", text or "").strip()


def strip_gutenberg_boilerplate(text: str | None) -> str:
    cleaned = clean_text(text)
    cleaned = re.sub(
        r"\*\*\*\s*START OF.*?\*\*\*",
        " ",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"\*\*\*\s*END OF.*",
        " ",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return clean_text(cleaned)


def normalize_list(value: Any, *, max_items: int | None = MAX_TAGS) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = [value]
    else:
        try:
            items = list(value)
        except TypeError:
            items = [value]

    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = clean_text(str(item)).lower()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
        if max_items is not None and len(normalized) >= max_items:
            break
    return normalized


def make_summary(text: str | None) -> str:
    cleaned = strip_gutenberg_boilerplate(text)
    if len(cleaned) <= SUMMARY_CHARS:
        return cleaned
    return cleaned[:SUMMARY_CHARS].rstrip() + "..."


def infer_format(topics: list[str], subjects: list[str], text: str | None) -> str:
    joined = " ".join(topics + subjects).lower()
    word_count = len(clean_text(text).split())

    if "short stories" in joined or "short story" in joined:
        return "short_story"
    if word_count and word_count < 12_000:
        return "short_story"
    return "novel"


def infer_length_bucket(text: str | None) -> str:
    word_count = len(clean_text(text).split())
    if word_count < 20_000:
        return "short"
    if word_count < 70_000:
        return "medium"
    return "long"


def infer_audience_rating(subjects: list[str]) -> str:
    joined = " ".join(subjects).lower()
    if "juvenile fiction" in joined or "children" in joined:
        return "General"
    return "General"


def gutenberg_row_to_storyseek(row: dict[str, Any]) -> dict[str, Any]:
    text = strip_gutenberg_boilerplate(row.get("text"))
    topics = normalize_list(row.get("topics"))
    subjects = normalize_list(row.get("pg_subjects"))
    book_id = clean_text(str(row.get("book_id") or row.get("id") or "unknown"))

    title = clean_text(row.get("title")) or "Untitled"
    creator = clean_text(row.get("author")) or "Unknown"

    return {
        "work_id": f"pg_{book_id}",
        "title": title,
        "creator": creator,
        "format": infer_format(topics, subjects, text),
        "summary": make_summary(text),
        "genres": topics or ["fiction"],
        "themes": subjects,
        "tropes": [],
        "relationship_dynamics": [],
        "content_warnings": ["unknown"],
        "audience_rating": infer_audience_rating(subjects),
        "status": "Complete",
        "length_bucket": infer_length_bucket(text),
        "language": "English",
        "source": "project_gutenberg",
        "book_id": book_id,
        "pg_subjects": subjects,
        "topics": topics,
        "release_date": row.get("release_date"),
    }


def iter_gutenberg_rows(*, limit: int | None = None) -> Iterable[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: install `datasets` first, e.g. "
            "`pip install -r backend/requirements.txt`."
        ) from exc

    dataset = load_dataset(DATASET_NAME, DATASET_CONFIG, split=DATASET_SPLIT)
    for i, row in enumerate(dataset):
        if limit is not None and i >= limit:
            break
        yield dict(row)


def write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: set[str] = set()
    count = 0
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            doc = gutenberg_row_to_storyseek(row)
            work_id = doc["work_id"]
            if work_id in seen_ids:
                continue
            seen_ids.add(work_id)
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Despina/project_gutenberg fiction books to StorySeek JSONL."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=None, help="Convert only the first N books.")
    args = parser.parse_args()

    count = write_jsonl(iter_gutenberg_rows(limit=args.limit), args.out)
    print(f"Wrote {count} Gutenberg works to {args.out}")


if __name__ == "__main__":
    main()
