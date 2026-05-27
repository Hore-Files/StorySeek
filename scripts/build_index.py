"""Create the OpenSearch index and bulk-load works.jsonl.

Usage:
    python scripts/build_index.py             # build a new version and swap alias
    python scripts/build_index.py --recreate  # same alias-safe rebuild flow
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
from backend.app.opensearch_client import (  # noqa: E402
    alias_targets,
    ensure_index,
    get_client,
    swap_alias,
    versioned_index_name,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the StorySeek OpenSearch index.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Build a fresh versioned index and atomically swap the search alias.",
    )
    parser.add_argument("--path", type=Path, default=None, help="Override path to works.jsonl.")
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="Delete indexes that previously pointed at the alias after a successful swap.",
    )
    args = parser.parse_args()

    settings = get_settings()
    path = args.path or settings.data_path
    if not path.exists():
        raise SystemExit(f"Data file not found: {path}")

    alias = settings.search_index
    client = get_client()
    old_targets = alias_targets(alias)
    target_index = versioned_index_name(alias)

    ensure_index(index=target_index, recreate=False)
    n = bulk_index(path, index=target_index)

    count = client.count(index=target_index)["count"]
    if count != n:
        raise SystemExit(
            f"Indexed count mismatch for '{target_index}': bulk reported {n}, count API returned {count}. "
            f"Alias '{alias}' was not changed."
        )

    swap_alias(alias, target_index)
    print(f"Indexed {n} docs from {path} into '{target_index}'.")
    print(f"Alias '{alias}' now points to '{target_index}'.")

    if args.delete_old:
        for old_index in old_targets:
            if old_index != target_index and client.indices.exists(index=old_index):
                client.indices.delete(index=old_index)
                print(f"Deleted old index '{old_index}'.")


if __name__ == "__main__":
    main()
