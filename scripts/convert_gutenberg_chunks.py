"""Convert Project Gutenberg content into content-search JSONL.

This script intentionally defaults to a bounded demo subset. The full
fiction_books_in_chunks split is very large, so start small and scale up only
after quality checks pass.

Usage:
    python scripts/convert_gutenberg_chunks.py
    python scripts/convert_gutenberg_chunks.py --source data/sample/works_gutenberg.jsonl
    python scripts/convert_gutenberg_chunks.py --book-limit 100 --max-chunks-per-book 50
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.convert_gutenberg_to_storyseek import (
    clean_text,
    infer_format,
    infer_length_bucket,
    make_summary,
    normalize_list,
)

DEFAULT_OUT = REPO_ROOT / "data" / "processed" / "gutenberg_chunks.jsonl"
DEFAULT_SOURCE = REPO_ROOT / "data" / "sample" / "works_gutenberg.jsonl"
DATASET_NAME = "Despina/project_gutenberg"
BOOKS_CONFIG = "fiction_books"
CHUNKS_CONFIG = "fiction_books_in_chunks"
DATASET_SPLIT = "train"
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

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


def clean_chunk_text(text: str | None) -> str:
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


def is_boilerplate_chunk(text: str | None, *, min_chars: int = 80) -> bool:
    cleaned = clean_chunk_text(text)
    lowered = cleaned.lower()
    if len(cleaned) < min_chars:
        return True
    if any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in BOILERPLATE_PATTERNS):
        return True
    alpha_ratio = sum(ch.isalpha() for ch in cleaned) / max(len(cleaned), 1)
    return alpha_ratio < 0.55


def _load_dataset(config: str):
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: install `datasets` first, e.g. "
            "`pip install -r backend/requirements.txt`."
        ) from exc
    return load_dataset(DATASET_NAME, config, split=DATASET_SPLIT)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _metadata_from_work(row: dict[str, Any]) -> dict[str, Any]:
    work_id = clean_text(row.get("work_id")) or "unknown"
    return {
        "work_id": work_id,
        "book_id": clean_text(row.get("book_id")) or work_id.removeprefix("pg_").removeprefix("g_"),
        "title": clean_text(row.get("title")) or "Untitled",
        "creator": clean_text(row.get("creator") or row.get("author")) or "Unknown",
        "format": row.get("format") or "novel",
        "summary": clean_text(row.get("summary")),
        "genres": normalize_list(row.get("genres") or row.get("topics")) or ["fiction"],
        "themes": normalize_list(row.get("themes") or row.get("pg_subjects")),
        "tropes": normalize_list(row.get("tropes")),
        "relationship_dynamics": normalize_list(row.get("relationship_dynamics")),
        "content_warnings": normalize_list(row.get("content_warnings")) or ["unknown"],
        "audience_rating": row.get("audience_rating") or "General",
        "status": row.get("status") or "Complete",
        "length_bucket": row.get("length_bucket") or infer_length_bucket(row.get("text", "")),
        "language": row.get("language") or "English",
        "source": row.get("source") or "project_gutenberg",
        "pg_subjects": normalize_list(row.get("pg_subjects") or row.get("themes")),
        "topics": normalize_list(row.get("topics") or row.get("genres")),
        "release_date": row.get("release_date"),
    }


def split_text_into_chunks(
    text: str | None,
    *,
    sentences_per_chunk: int = 5,
    overlap_sentences: int = 1,
) -> Iterable[tuple[int, str]]:
    cleaned = clean_chunk_text(text)
    sentences = [s.strip() for s in SENTENCE_RE.split(cleaned) if s.strip()]
    if not sentences:
        return
    step = max(1, sentences_per_chunk - overlap_sentences)
    for start in range(0, len(sentences), step):
        chunk = " ".join(sentences[start : start + sentences_per_chunk]).strip()
        if chunk:
            yield start, chunk


def build_book_metadata(book_limit: int | None = 500) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(_load_dataset(BOOKS_CONFIG)):
        if book_limit is not None and i >= book_limit:
            break
        book_id = clean_text(str(row.get("book_id") or row.get("id") or "unknown"))
        topics = normalize_list(row.get("topics"))
        subjects = normalize_list(row.get("pg_subjects"))
        text = row.get("text", "")
        metadata[book_id] = {
            "work_id": f"pg_{book_id}",
            "book_id": book_id,
            "title": clean_text(row.get("title")) or "Untitled",
            "creator": clean_text(row.get("author")) or "Unknown",
            "format": infer_format(topics, subjects, text),
            "summary": make_summary(text),
            "genres": topics or ["fiction"],
            "themes": subjects,
            "tropes": [],
            "relationship_dynamics": [],
            "content_warnings": ["unknown"],
            "audience_rating": "General",
            "status": "Complete",
            "length_bucket": infer_length_bucket(text),
            "language": "English",
            "source": "project_gutenberg",
            "pg_subjects": subjects,
            "topics": topics,
            "release_date": row.get("release_date"),
        }
    return metadata


def chunk_row_to_doc(row: dict[str, Any], metadata: dict[str, Any], *, min_chars: int = 80) -> dict[str, Any] | None:
    text_chunk = clean_chunk_text(row.get("text_chunk"))
    if is_boilerplate_chunk(text_chunk, min_chars=min_chars):
        return None

    book_id = metadata["book_id"]
    chunk_index = int(row.get("chunk_index") or 0)
    return {
        "chunk_id": f"pg_{book_id}_c{chunk_index:06d}",
        "work_id": metadata["work_id"],
        "book_id": book_id,
        "chunk_index": chunk_index,
        "title": metadata["title"],
        "creator": metadata["creator"],
        "genres": metadata["genres"],
        "themes": metadata["themes"],
        "text_chunk": text_chunk,
        "source": "project_gutenberg",
        "combined_text": " ".join(
            [
                metadata["title"],
                metadata["creator"],
                " ".join(metadata["genres"]),
                " ".join(metadata["themes"]),
                text_chunk,
            ]
        ),
    }


def iter_chunk_docs(
    *,
    book_limit: int | None = 500,
    max_chunks_per_book: int | None = 100,
    min_chars: int = 80,
) -> Iterable[dict[str, Any]]:
    metadata_by_book = build_book_metadata(book_limit)
    kept_per_book: dict[str, int] = defaultdict(int)

    for row in _load_dataset(CHUNKS_CONFIG):
        book_id = clean_text(str(row.get("book_id") or "unknown"))
        metadata = metadata_by_book.get(book_id)
        if not metadata:
            continue
        if max_chunks_per_book is not None and kept_per_book[book_id] >= max_chunks_per_book:
            continue
        doc = chunk_row_to_doc(dict(row), metadata, min_chars=min_chars)
        if doc is None:
            continue
        kept_per_book[book_id] += 1
        yield doc


def iter_chunk_docs_from_works(
    source: Path,
    *,
    book_limit: int | None = 500,
    max_chunks_per_book: int | None = 100,
    min_chars: int = 80,
    sentences_per_chunk: int = 5,
    overlap_sentences: int = 1,
) -> Iterable[dict[str, Any]]:
    for i, row in enumerate(_iter_jsonl(source)):
        if book_limit is not None and i >= book_limit:
            break
        metadata = _metadata_from_work(row)
        text = row.get("text") or row.get("content") or row.get("full_text") or row.get("summary")
        kept = 0
        for chunk_index, text_chunk in split_text_into_chunks(
            text,
            sentences_per_chunk=sentences_per_chunk,
            overlap_sentences=overlap_sentences,
        ):
            if max_chunks_per_book is not None and kept >= max_chunks_per_book:
                break
            doc = chunk_row_to_doc(
                {"chunk_index": chunk_index, "text_chunk": text_chunk},
                metadata,
                min_chars=min_chars,
            )
            if doc is None:
                continue
            kept += 1
            yield doc


def write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Gutenberg content chunks to JSONL.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="StorySeek work-level JSONL with a text/content field. Used by default.",
    )
    parser.add_argument(
        "--from-hf-chunks",
        action="store_true",
        help="Use HuggingFace fiction_books_in_chunks instead of chunking the local works JSONL.",
    )
    parser.add_argument("--book-limit", type=int, default=500)
    parser.add_argument("--max-chunks-per-book", type=int, default=100)
    parser.add_argument("--min-chars", type=int, default=80)
    parser.add_argument("--sentences-per-chunk", type=int, default=5)
    parser.add_argument("--overlap-sentences", type=int, default=1)
    args = parser.parse_args()

    rows = (
        iter_chunk_docs(
            book_limit=args.book_limit,
            max_chunks_per_book=args.max_chunks_per_book,
            min_chars=args.min_chars,
        )
        if args.from_hf_chunks
        else iter_chunk_docs_from_works(
            args.source,
            book_limit=args.book_limit,
            max_chunks_per_book=args.max_chunks_per_book,
            min_chars=args.min_chars,
            sentences_per_chunk=args.sentences_per_chunk,
            overlap_sentences=args.overlap_sentences,
        )
    )
    count = write_jsonl(
        rows,
        args.out,
    )
    print(f"Wrote {count} Gutenberg chunks to {args.out}")


if __name__ == "__main__":
    main()
