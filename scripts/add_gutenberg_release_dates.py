"""Add Project Gutenberg release dates to StorySeek Gutenberg works JSONL.

The script preserves all existing fields and only adds/updates `release_date`
when a matching Gutenberg `book_id` is found in the HuggingFace fiction_books
metadata.

Usage:
    python scripts/add_gutenberg_release_dates.py
    python scripts/add_gutenberg_release_dates.py --input data/sample/works_gutenberg.jsonl --in-place
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATASET_NAME = "Despina/project_gutenberg"
BOOKS_CONFIG = "fiction_books"
DATASET_SPLIT = "train"
DEFAULT_INPUT = REPO_ROOT / "data" / "sample" / "works_gutenberg.jsonl"
HF_SNAPSHOT_ID = "883396575e060611e74f27f1f331a9eab1c2ca80"


def gutenberg_id_from_work(row: dict[str, Any]) -> str | None:
    if row.get("book_id"):
        return str(row["book_id"]).strip()
    match = re.search(r"(?:pg|g)_(\d+)", str(row.get("work_id", "")), flags=re.IGNORECASE)
    return match.group(1) if match else None


def load_release_dates_from_cached_parquet() -> dict[str, str]:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return {}

    parquet_dir = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "datasets--Despina--project_gutenberg"
        / "snapshots"
        / HF_SNAPSHOT_ID
        / "fiction_books"
    )
    if not parquet_dir.exists():
        return {}

    release_dates: dict[str, str] = {}
    for parquet_path in sorted(parquet_dir.glob("*.parquet")):
        table = pq.ParquetFile(parquet_path).read(columns=["book_id", "release_date"])
        for row in table.to_pylist():
            book_id = str(row.get("book_id") or "").strip()
            release_date = str(row.get("release_date") or "").strip()
            if book_id and release_date:
                release_dates[book_id] = release_date
    return release_dates


def load_release_dates() -> dict[str, str]:
    cached = load_release_dates_from_cached_parquet()
    if cached:
        return cached

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: install `datasets` first, e.g. "
            "`pip install -r backend/requirements.txt`."
        ) from exc

    dataset = load_dataset(DATASET_NAME, BOOKS_CONFIG, split=DATASET_SPLIT)
    release_dates: dict[str, str] = {}
    for row in dataset:
        book_id = str(row.get("book_id") or row.get("id") or "").strip()
        release_date = str(row.get("release_date") or "").strip()
        if book_id and release_date:
            release_dates[book_id] = release_date
    return release_dates


def merge_release_dates(input_path: Path, output_path: Path) -> tuple[int, int]:
    release_dates = load_release_dates()
    total = 0
    updated = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            row = json.loads(line)
            total += 1
            book_id = gutenberg_id_from_work(row)
            release_date = release_dates.get(book_id or "")
            if release_date:
                row["release_date"] = release_date
                updated += 1
            dst.write(json.dumps(row, ensure_ascii=False) + "\n")
    return total, updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge release_date into Gutenberg works JSONL.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--in-place", action="store_true", help="Overwrite input after creating a .bak backup.")
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    if args.in_place:
        backup = args.input.with_suffix(args.input.suffix + ".bak")
        temp = args.input.with_suffix(args.input.suffix + ".tmp")
        shutil.copy2(args.input, backup)
        total, updated = merge_release_dates(args.input, temp)
        temp.replace(args.input)
        print(f"Updated {updated}/{total} works in {args.input}")
        print(f"Backup written to {backup}")
        return

    output = args.output or args.input.with_name(args.input.stem + "_with_release_dates.jsonl")
    total, updated = merge_release_dates(args.input, output)
    print(f"Updated {updated}/{total} works")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
