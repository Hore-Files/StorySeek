from __future__ import annotations

from backend.app.schemas import SearchFilters, SearchRequest, Work
from backend.app.search.explain import explain_hit


def test_explain_hit_mentions_query_overlap_filters_and_warning_exclusion():
    work = Work(
        work_id="w_1",
        title="The Healing Letter",
        creator="Author",
        format="novel",
        summary="A slow burn story about found family.",
        genres=["romance"],
        themes=["healing"],
        tropes=["slow burn", "found family"],
        relationship_dynamics=["rivals"],
        content_warnings=["none"],
        audience_rating="Teen",
        status="Complete",
        length_bucket="medium",
    )
    req = SearchRequest(
        query="slow burn healing",
        filters=SearchFilters(tropes=["slow burn"], themes=["healing"]),
        exclude_warnings=["major character death"],
    )

    explanation = explain_hit(work, req)

    joined = " ".join(explanation).lower()
    assert "slow" in joined or "burn" in joined
    assert "slow burn" in joined
    assert "healing" in joined
    assert "excluded warning" in joined
