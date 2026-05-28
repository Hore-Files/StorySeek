from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from opensearchpy.helpers import bulk

from .config import get_settings
from .embeddings import embed_texts
from .opensearch_client import build_combined_text, get_client

RAW_TEXT_FIELDS = {"text", "content", "full_text"}
BULK_CHUNK_SIZE = 8
BULK_MAX_CHUNK_BYTES = 10 * 1024 * 1024


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
            # Keep the canonical JSONL intact, but do not store full-book text in
            # the work index. Large raw text fields can make OpenSearch reject
            # bulk requests and are better indexed through the chunk index.
            enriched = {k: v for k, v in doc.items() if k not in RAW_TEXT_FIELDS}
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


def bulk_index(path: Path, index: str | None = None) -> int:
    client = get_client()
    index = index or get_settings().search_index
    success, _ = bulk(
        client,
        _actions(iter_jsonl(path), index),
        refresh=True,
        chunk_size=BULK_CHUNK_SIZE,
        max_chunk_bytes=BULK_MAX_CHUNK_BYTES,
    )
    return success
