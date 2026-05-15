from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from opensearchpy.helpers import bulk

from .config import get_settings
from .embeddings import embed_texts
from .opensearch_client import build_combined_text, get_client


def iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _actions(docs: Iterable[dict], index: str) -> Iterator[dict]:
    batch_docs: list[dict] = []
    batch_texts: list[str] = []

    def flush() -> Iterator[dict]:
        if not batch_docs:
            return iter(())
        embeddings = embed_texts(batch_texts)
        for doc, combined_text, emb in zip(batch_docs, batch_texts, embeddings, strict=True):
            enriched = dict(doc)
            enriched["combined_text"] = combined_text
            enriched["embedding"] = emb
            yield {
                "_op_type": "index",
                "_index": index,
                "_id": doc["work_id"],
                "_source": enriched,
            }

    for doc in docs:
        batch_docs.append(doc)
        batch_texts.append(build_combined_text(doc))
        if len(batch_docs) >= 32:
            yield from flush()
            batch_docs.clear()
            batch_texts.clear()

    if batch_docs:
        yield from flush()


def bulk_index(path: Path) -> int:
    client = get_client()
    index = get_settings().opensearch_index
    success, _ = bulk(client, _actions(iter_jsonl(path), index), refresh=True)
    return success
