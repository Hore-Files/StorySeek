"""Create the OpenSearch index and bulk-load works.jsonl.

Usage:
    python scripts/build_index.py             # create-if-missing, then index
    python scripts/build_index.py --recreate  # drop existing index first
    python scripts/build_index.py --path other/works.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a script (no package install) by making the repo root importable.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import get_settings  # noqa: E402
from backend.app.data_loader import bulk_index  # noqa: E402
from backend.app.opensearch_client import ensure_index, get_client  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the StorySeek OpenSearch index.")
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate the index first.")
    parser.add_argument("--path", type=Path, default=None, help="Override path to works.jsonl.")
    args = parser.parse_args()

    settings = get_settings()
    path = args.path or settings.data_path
    if not path.exists():
        raise SystemExit(f"Data file not found: {path}")

    ensure_index(recreate=args.recreate)
    n = bulk_index(path)

    client = get_client()
    count = client.count(index=settings.opensearch_index)["count"]
    print(f"Indexed {n} docs from {path} into '{settings.opensearch_index}' (total now: {count}).")


if __name__ == "__main__":
    main()
