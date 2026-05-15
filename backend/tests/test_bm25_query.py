"""Tests for the BM25 query builder.

These do not hit OpenSearch — they assert the shape of the DSL that we send,
which is the contract we care about.
"""
from __future__ import annotations

from backend.app.schemas import SearchFilters, SearchRequest
from backend.app.search.bm25 import build_bm25_query


def _bool(body: dict) -> dict:
    return body["query"]["bool"]


def test_empty_query_uses_match_all():
    body = build_bm25_query(SearchRequest(query=""))
    assert _bool(body)["must"] == [{"match_all": {}}]


def test_text_query_multi_match_fields():
    body = build_bm25_query(SearchRequest(query="rivals to lovers"))
    mm = _bool(body)["must"][0]["multi_match"]
    assert mm["query"] == "rivals to lovers"
    fields = set(mm["fields"])
    assert {"title^3", "summary^2", "tropes^2", "combined_text"} <= fields


def test_exclude_warnings_goes_to_must_not():
    body = build_bm25_query(
        SearchRequest(query="anything", exclude_warnings=["major character death", "abuse"])
    )
    must_not = _bool(body)["must_not"]
    assert must_not == [{"terms": {"content_warnings": ["major character death", "abuse"]}}]


def test_tropes_are_and_not_or():
    """Selecting multiple tropes should require ALL of them on each hit (AND)."""
    body = build_bm25_query(
        SearchRequest(
            query="",
            filters=SearchFilters(tropes=["slow burn", "found family"]),
        )
    )
    filters = _bool(body)["filter"]
    trope_clauses = [c for c in filters if "term" in c and "tropes" in c["term"]]
    assert {c["term"]["tropes"] for c in trope_clauses} == {"slow burn", "found family"}
    # And no single `terms` clause sneaking back in for tropes:
    assert not any("terms" in c and "tropes" in c.get("terms", {}) for c in filters)


def test_themes_are_and_not_or():
    body = build_bm25_query(
        SearchRequest(
            query="",
            filters=SearchFilters(themes=["dark academia", "political intrigue"]),
        )
    )
    filters = _bool(body)["filter"]
    theme_clauses = [c for c in filters if "term" in c and "themes" in c["term"]]
    assert {c["term"]["themes"] for c in theme_clauses} == {"dark academia", "political intrigue"}


def test_facet_filters_are_or():
    """Format/genres/status are conventionally OR (any of selected values)."""
    body = build_bm25_query(
        SearchRequest(
            query="",
            filters=SearchFilters(
                formats=["novel", "short_story"],
                genres=["fantasy", "mystery"],
                statuses=["Complete"],
            ),
        )
    )
    filters = _bool(body)["filter"]
    assert {"terms": {"format": ["novel", "short_story"]}} in filters
    assert {"terms": {"genres": ["fantasy", "mystery"]}} in filters
    assert {"terms": {"status": ["Complete"]}} in filters


def test_pagination_offsets():
    body = build_bm25_query(SearchRequest(query="a", page=3, size=15))
    assert body["from"] == 30
    assert body["size"] == 15


def test_combined_text_excluded_from_source():
    body = build_bm25_query(SearchRequest(query="a"))
    assert body["_source"]["excludes"] == ["combined_text", "embedding"]
