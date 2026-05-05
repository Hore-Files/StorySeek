from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from opensearchpy.helpers import bulk

from .config import get_settings
from .opensearch_client import build_combined_text, get_client


def iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _actions(docs: Iterable[dict], index: str) -> Iterator[dict]:
    for doc in docs:
        enriched = dict(doc)
        enriched["combined_text"] = build_combined_text(doc)
        yield {
            "_op_type": "index",
            "_index": index,
            "_id": doc["work_id"],
            "_source": enriched,
        }


def bulk_index(path: Path) -> int:
    client = get_client()
    index = get_settings().opensearch_index
    success, _ = bulk(client, _actions(iter_jsonl(path), index), refresh=True)
    return success
