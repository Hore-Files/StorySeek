"""Create the OpenSearch chunk index and bulk-load Gutenberg chunks.

Usage:
    python scripts/build_chunk_index.py --recreate
    python scripts/build_chunk_index.py --path data/processed/gutenberg_chunks.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.chunk_loader import bulk_index_chunks  # noqa: E402
from backend.app.config import get_settings  # noqa: E402
from backend.app.opensearch_client import ensure_chunk_index, get_client  # noqa: E402

DEFAULT_PATH = REPO_ROOT / "data" / "processed" / "gutenberg_chunks.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the StorySeek Gutenberg chunk index.")
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate the chunk index first.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"Chunk file not found: {args.path}")

    ensure_chunk_index(recreate=args.recreate)
    n = bulk_index_chunks(args.path)

    settings = get_settings()
    client = get_client()
    count = client.count(index=settings.opensearch_chunks_index)["count"]
    print(f"Indexed {n} chunks from {args.path} into '{settings.opensearch_chunks_index}' (total now: {count}).")


if __name__ == "__main__":
    main()
