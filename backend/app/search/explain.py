from __future__ import annotations

import re

from ..schemas import SearchRequest, Work

_TOKEN_RE = re.compile(r"[A-Za-z']+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "")}


def _tag_matches(tags: list[str], query_tokens: set[str]) -> list[str]:
    matched = []
    for tag in tags:
        tag_tokens = _tokens(tag)
        if tag_tokens & query_tokens:
            matched.append(tag)
    return matched


def explain_hit(work: Work, req: SearchRequest) -> list[str]:
    """Produce a small bullet list explaining why `work` matched `req`.

    Rules:
      - For each tag field, list tags that share a token with the query.
      - For requested facet filters (tropes/genres/themes), list confirmations.
      - For each excluded warning, confirm the work does not contain it.
    """
    bullets: list[str] = []
    query_tokens = _tokens(req.query)

    for field_label, tags in (
        ("trope", work.tropes),
        ("theme", work.themes),
        ("genre", work.genres),
        ("relationship", work.relationship_dynamics),
    ):
        for tag in _tag_matches(tags, query_tokens):
            bullets.append(f"Matches {field_label}: {tag}")

    f = req.filters
    for tag in f.tropes:
        if tag in work.tropes:
            bullets.append(f"Matches requested trope: {tag}")
    for tag in f.genres:
        if tag in work.genres:
            bullets.append(f"Matches requested genre: {tag}")
    for tag in f.themes:
        if tag in work.themes:
            bullets.append(f"Matches requested theme: {tag}")

    for w in req.exclude_warnings:
        if w not in work.content_warnings:
            bullets.append(f"Does not contain excluded warning: {w}")

    if not bullets:
        bullets.append("Matched on title or summary text")

    # Deduplicate while preserving order.
    seen = set()
    deduped = []
    for b in bullets:
        if b not in seen:
            seen.add(b)
            deduped.append(b)
    return deduped
