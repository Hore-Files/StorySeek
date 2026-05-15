"""StorySeek Streamlit UI.

Run with:
    streamlit run frontend/streamlit_app.py
"""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

FORMATS = ["novel", "short_story", "fanfic_style", "manga", "webnovel"]
GENRES = [
    "fantasy", "mystery", "romance", "science fiction", "horror",
    "historical", "adventure", "drama", "comedy",
]
THEMES = [
    "dark academia", "political intrigue", "healing", "revenge", "redemption",
    "grief", "betrayal", "friendship", "identity", "coming of age",
]
TROPES = [
    "slow burn", "enemies to lovers", "rivals to lovers", "found family",
    "fake dating", "forbidden magic", "time loop", "chosen one",
    "villain redemption", "academy setting", "kingdom building",
    "mutual pining", "hurt/comfort",
]
CONTENT_WARNINGS = [
    "major character death", "graphic violence", "abuse", "self harm",
]
STATUSES = ["Complete", "Ongoing", "Hiatus"]
LENGTHS = ["short", "medium", "long"]
AUDIENCES = ["General", "Teen", "Mature"]


def post_search(payload: dict) -> dict[str, Any]:
    resp = requests.post(f"{BACKEND_URL}/search", json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_similar(work_id: str, size: int = 5) -> dict[str, Any]:
    resp = requests.get(f"{BACKEND_URL}/similar/{work_id}", params={"size": size}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _render_hit(hit: dict, key_prefix: str) -> None:
    work = hit["work"]
    score = hit.get("score", 0.0)
    explanation = hit.get("explanation", [])

    with st.container(border=True):
        st.markdown(f"### {work['title']}")
        meta_line = " · ".join(
            [
                work["format"],
                work["status"],
                work["length_bucket"],
                work["audience_rating"],
                f"score {score:.2f}",
            ]
        )
        st.caption(meta_line)
        st.write(work["summary"])

        tag_cols = st.columns(3)
        with tag_cols[0]:
            if work.get("genres"):
                st.markdown("**Genres**  \n" + ", ".join(work["genres"]))
        with tag_cols[1]:
            if work.get("tropes"):
                st.markdown("**Tropes**  \n" + ", ".join(work["tropes"]))
        with tag_cols[2]:
            if work.get("themes"):
                st.markdown("**Themes**  \n" + ", ".join(work["themes"]))

        warnings = [w for w in work.get("content_warnings", []) if w != "none"]
        if warnings:
            st.markdown(":warning: **Content warnings:** " + ", ".join(warnings))
        else:
            st.markdown(":white_check_mark: No listed content warnings")

        if explanation:
            with st.expander("Why this matched"):
                for bullet in explanation:
                    st.markdown(f"- {bullet}")

        if st.button("More like this", key=f"{key_prefix}_{work['work_id']}"):
            st.session_state["similar_for"] = work["work_id"]
            st.session_state["similar_title"] = work["title"]


def main() -> None:
    st.set_page_config(page_title="StorySeek", layout="wide")
    st.title("StorySeek")
    st.caption(
        "Semantic discovery for fiction. Search by natural-language descriptions of "
        "tropes, themes, dynamics, format, and content."
    )

    with st.sidebar:
        st.header("Filters")
        mode = st.radio(
            "Retrieval mode",
            options=["BM25", "Dense", "Hybrid (coming soon)"],
            index=0,
            help="Dense retrieval is available; hybrid is still coming soon.",
        )
        sel_formats = st.multiselect("Format", FORMATS)
        sel_genres = st.multiselect("Genres", GENRES)
        sel_tropes = st.multiselect("Must include tropes", TROPES)
        sel_themes = st.multiselect("Must include themes", THEMES)
        sel_statuses = st.multiselect("Status", STATUSES)
        sel_lengths = st.multiselect("Length", LENGTHS)
        sel_audiences = st.multiselect("Audience rating", AUDIENCES)
        sel_exclude = st.multiselect("Exclude content warnings", CONTENT_WARNINGS)
        size = st.slider("Results per page", min_value=5, max_value=30, value=10)

    query = st.text_input(
        "Describe the story you want",
        value="slow burn rivals to lovers with found family",
        placeholder="dark academia mystery with political intrigue and forbidden magic",
    )

    if mode == "Hybrid (coming soon)":
        st.info("Hybrid mode is coming soon. Falling back to BM25.")

    mode_value = "dense" if mode == "Dense" else "bm25"

    payload = {
        "query": query,
        "mode": mode_value,
        "page": 1,
        "size": size,
        "exclude_warnings": sel_exclude,
        "filters": {
            "formats": sel_formats,
            "genres": sel_genres,
            "tropes": sel_tropes,
            "themes": sel_themes,
            "statuses": sel_statuses,
            "length_buckets": sel_lengths,
            "audience_ratings": sel_audiences,
            "languages": [],
        },
    }

    if st.button("Search", type="primary") or query:
        try:
            result = post_search(payload)
        except requests.RequestException as exc:
            st.error(f"Backend error: {exc}")
            return

        st.caption(f"{result['total']} results · mode {result['mode']}")
        for i, hit in enumerate(result["hits"]):
            _render_hit(hit, key_prefix=f"main_{i}")

    sid = st.session_state.get("similar_for")
    if sid:
        st.divider()
        st.subheader(f"More like: {st.session_state.get('similar_title', sid)}")
        try:
            similar = get_similar(sid, size=5)
        except requests.RequestException as exc:
            st.error(f"Backend error: {exc}")
            return
        for i, hit in enumerate(similar["hits"]):
            _render_hit(hit, key_prefix=f"similar_{i}")


if __name__ == "__main__":
    main()
