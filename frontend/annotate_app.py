"""StorySeek Relevance Annotator Tool.

Run with:
    streamlit run frontend/annotate_app.py --server.port 8502
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def load_queries() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[1] / "data" / "eval" / "queries.jsonl"
    if not path.exists():
        st.error(f"Queries file not found at {path}")
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_existing_qrels() -> dict[str, dict[str, int]]:
    path = Path(__file__).resolve().parents[1] / "data" / "eval" / "hand_labeled_qrels.csv"
    if not path.exists():
        return {}
    qrels: dict[str, dict[str, int]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            _ = next(reader)  # skip header
        except StopIteration:
            return {}
        for row in reader:
            if len(row) >= 3:
                qid, wid, rel = row[0], row[1], int(row[2])
                qrels.setdefault(qid, {})[wid] = rel
    return qrels


def save_qrel(qid: str, wid: str, rel: int | None) -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "eval" / "hand_labeled_qrels.csv"
    
    # Load all existing
    all_qrels: dict[tuple[str, str], int] = {}
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                _ = next(reader)  # skip header
            except StopIteration:
                pass
            else:
                for row in reader:
                    if len(row) >= 3:
                        all_qrels[(row[0], row[1])] = int(row[2])
                        
    # Update, add, or delete the relevance
    if rel is None:
        all_qrels.pop((qid, wid), None)
    else:
        all_qrels[(qid, wid)] = rel
    
    # Write back
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "work_id", "relevance"])
        for (q, w), r in sorted(all_qrels.items(), key=lambda x: x[0]):
            writer.writerow([q, w, r])


def fetch_candidates(query_text: str, exclude_warnings: list[str]) -> list[dict[str, Any]]:
    """Build candidates on the fly by combining top 20 BM25 and top 20 Dense hits."""
    candidates: dict[str, dict[str, Any]] = {}
    
    def search_mode(mode: str) -> None:
        payload = {
            "query": query_text,
            "mode": mode,
            "page": 1,
            "size": 20,
            "exclude_warnings": exclude_warnings,
            "filters": {
                "formats": [],
                "genres": [],
                "tropes": [],
                "themes": [],
                "statuses": [],
                "length_buckets": [],
                "audience_ratings": [],
                "languages": [],
            },
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/search", json=payload, timeout=15)
            resp.raise_for_status()
            hits = resp.json().get("hits", [])
            for h in hits:
                work = h["work"]
                candidates[work["work_id"]] = work
        except Exception as e:
            st.error(f"Error fetching {mode} candidates: {e}")

    # Union BM25 and Dense hits
    search_mode("bm25")
    search_mode("dense")
    
    # Sort candidate works by their ID to ensure a stable ordering
    return [candidates[wid] for wid in sorted(candidates.keys())]


def main() -> None:
    st.set_page_config(page_title="StorySeek Relevance Annotator", layout="wide")
    
    # Inject Custom Styling for premium aesthetic
    st.markdown(
        """
        <style>
        .reportview-container {
            background-color: #0e1117;
        }
        .main-header {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF4B4B 0%, #1A2238 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }
        .subheader {
            color: #8fa1b3;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        .work-card {
            background-color: #161b22;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #30363d;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
        }
        .metadata-pill {
            background-color: #21262d;
            color: #c9d1d9;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-right: 8px;
            border: 1px solid #30363d;
            display: inline-block;
        }
        .tag-pill {
            background-color: rgba(56, 139, 253, 0.15);
            color: #58a6ff;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-right: 6px;
            margin-bottom: 6px;
            display: inline-block;
            border: 1px solid rgba(56, 139, 253, 0.3);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-header">StorySeek Relevance Annotator</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Internal development tool to manually establish Gold Standard judgments for the evaluation harness.</div>', unsafe_allow_html=True)

    # Check live API connection
    try:
        health_resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        backend_ok = health_resp.status_code == 200
    except Exception:
        backend_ok = False

    if not backend_ok:
        st.error(f"❌ Cannot connect to StorySeek API backend at `{BACKEND_URL}`.")
        st.info("💡 Please start the backend service first (e.g. `uvicorn backend.app.main:app --port 8000`) before running this tool.")
        st.stop()

    # Load Queries
    queries = load_queries()
    if not queries:
        st.stop()

    # Layout: Sidebar controls
    with st.sidebar:
        st.header("Annotation Settings")
        selected_query = st.selectbox(
            "Select Search Query to Annotate",
            options=queries,
            format_func=lambda q: f"[{q['query_id']}] {q['query']}",
        )
        
        # Track active query change and reset local session state index
        qid = selected_query["query_id"]
        if "last_query_id" not in st.session_state or st.session_state["last_query_id"] != qid:
            st.session_state["active_idx"] = 0
            st.session_state["last_query_id"] = qid

        st.divider()
        st.markdown(
            """
            ### Grading Rubric
            * **Grade 3 (Highly Relevant):** Complete thematic & narrative fit. Fits tropes, tone, and warnings perfectly.
            * **Grade 2 (Relevant):** Good fit. Covers the main dynamic/theme, though minor elements may differ.
            * **Grade 1 (Marginally Relevant):** Very light connection. Single matching trope but different narrative direction.
            * **Grade 0 (Irrelevant):** Zero thematic match or contains query-excluded warnings.
            """
        )

    # Fetch/build candidate pool on the fly
    candidates = fetch_candidates(selected_query["query"], selected_query.get("exclude_warnings", []))
    if not candidates:
        st.warning("No candidate works found in pool for this query.")
        st.stop()

    # Fetch existing judgments
    existing_qrels = load_existing_qrels()
    query_judgments = existing_qrels.get(qid, {})

    # Show Progress Overview
    total_candidates = len(candidates)
    graded_count = sum(1 for c in candidates if c["work_id"] in query_judgments)
    progress_percentage = graded_count / total_candidates if total_candidates > 0 else 0.0

    st.subheader(f"Query: \"{selected_query['query']}\"")
    col_p1, col_p2 = st.columns([4, 1])
    with col_p1:
        st.progress(progress_percentage)
    with col_p2:
        st.markdown(f"**{graded_count} / {total_candidates} graded** ({progress_percentage*100:.0f}%)")

    # Main area: Split into a list panel and the active story card
    col_list, col_card = st.columns([1, 2])

    # Left list panel: list all candidates and show their grading status
    with col_list:
        st.markdown("### Candidate Pool")
        for i, cand in enumerate(candidates):
            wid = cand["work_id"]
            title = cand["title"]
            
            # Label prefix
            if wid in query_judgments:
                prefix = f"✅ [{query_judgments[wid]}]"
            else:
                prefix = "⏳ [Ungraded]"
            
            label = f"{prefix} {wid}: {title}"
            
            # Bold the currently active candidate
            if i == st.session_state["active_idx"]:
                st.markdown(f"👉 **{label}**")
            else:
                if st.button(label, key=f"select_{wid}", use_container_width=True):
                    st.session_state["active_idx"] = i
                    st.rerun()

    # Right main panel: Show details of the active story card and the grading controls
    active_idx = st.session_state["active_idx"]
    if active_idx >= len(candidates):
        st.session_state["active_idx"] = 0
        st.rerun()

    active_work = candidates[active_idx]
    active_wid = active_work["work_id"]

    with col_card:
        st.markdown("### Story Information")
        
        # Story card container HTML
        st.markdown(
            f"""
            <div class="work-card">
                <div style="font-size: 0.9rem; color: #8fa1b3; margin-bottom: 4px;">WORK ID: {active_wid}</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #ffffff; margin-bottom: 8px;">{active_work['title']}</div>
                <div style="font-size: 0.95rem; color: #a6b2c0; font-style: italic; margin-bottom: 16px;">by {active_work['creator']}</div>
                
                <div style="margin-bottom: 20px;">
                    <span class="metadata-pill">{active_work['format']}</span>
                    <span class="metadata-pill">{active_work['status']}</span>
                    <span class="metadata-pill">{active_work['length_bucket']}</span>
                    <span class="metadata-pill">{active_work['audience_rating']}</span>
                </div>
                
                <div style="font-size: 1.1rem; line-height: 1.6; color: #e1e4e8; margin-bottom: 24px;">
                    <strong>Summary:</strong><br>{active_work['summary']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tags rendering
        st.markdown("#### Tags & Attributes")
        tag_cols = st.columns(3)
        with tag_cols[0]:
            st.markdown("**Genres**")
            for genre in active_work.get("genres", []):
                st.markdown(f'<span class="tag-pill">{genre}</span>', unsafe_allow_html=True)
        with tag_cols[1]:
            st.markdown("**Tropes**")
            for trope in active_work.get("tropes", []):
                st.markdown(f'<span class="tag-pill">{trope}</span>', unsafe_allow_html=True)
        with tag_cols[2]:
            st.markdown("**Themes & Dynamics**")
            for theme in active_work.get("themes", []):
                st.markdown(f'<span class="tag-pill">{theme}</span>', unsafe_allow_html=True)
            for dyn in active_work.get("relationship_dynamics", []):
                st.markdown(f'<span class="tag-pill" style="background-color: rgba(227, 179, 65, 0.15); color: #e3b341; border: 1px solid rgba(227, 179, 65, 0.3);">{dyn}</span>', unsafe_allow_html=True)

        # Content Warnings
        warnings = [w for w in active_work.get("content_warnings", []) if w != "none"]
        if warnings:
            st.markdown(f"⚠️ **Content Warnings:** {', '.join(warnings)}")
        else:
            st.markdown("✅ No listed content warnings")

        st.divider()

        # Relevance Grading Controls
        st.markdown("### Assign Relevance Score")
        
        # Display current grade if exists
        current_grade = query_judgments.get(active_wid)
        if current_grade is not None:
            st.info(f"🏷️ Current relevance grade for this work: **{current_grade}**")
        else:
            st.warning("⏳ This work is currently **ungraded**.")

        # Grading buttons in a row
        btn_cols = st.columns(5)
        
        with btn_cols[0]:
            if st.button("0 - Irrelevant", type="secondary", use_container_width=True):
                save_qrel(qid, active_wid, 0)
                # Advance index automatically if not at end
                if active_idx < total_candidates - 1:
                    st.session_state["active_idx"] += 1
                st.rerun()

        with btn_cols[1]:
            if st.button("1 - Marginal", type="secondary", use_container_width=True):
                save_qrel(qid, active_wid, 1)
                if active_idx < total_candidates - 1:
                    st.session_state["active_idx"] += 1
                st.rerun()

        with btn_cols[2]:
            if st.button("2 - Relevant", type="secondary", use_container_width=True):
                save_qrel(qid, active_wid, 2)
                if active_idx < total_candidates - 1:
                    st.session_state["active_idx"] += 1
                st.rerun()

        with btn_cols[3]:
            if st.button("3 - Highly Relevant", type="primary", use_container_width=True):
                save_qrel(qid, active_wid, 3)
                if active_idx < total_candidates - 1:
                    st.session_state["active_idx"] += 1
                st.rerun()

        with btn_cols[4]:
            if current_grade is not None:
                if st.button("Clear Grade", type="secondary", use_container_width=True):
                    save_qrel(qid, active_wid, None)
                    st.rerun()

        # Keyboard/Manual Navigation buttons
        st.divider()
        nav_cols = st.columns(2)
        with nav_cols[0]:
            if st.button("⬅️ Previous Candidate", disabled=(active_idx == 0), use_container_width=True):
                st.session_state["active_idx"] -= 1
                st.rerun()
        with nav_cols[1]:
            if st.button("Next Candidate ➡️", disabled=(active_idx == total_candidates - 1), use_container_width=True):
                st.session_state["active_idx"] += 1
                st.rerun()


if __name__ == "__main__":
    main()
