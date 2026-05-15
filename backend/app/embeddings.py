"""Embedding helpers for dense retrieval."""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from sentence_transformers import SentenceTransformer

from .config import get_settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model_name)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


@lru_cache(maxsize=512)
def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
