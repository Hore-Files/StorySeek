from __future__ import annotations

import csv
import json

from backend.app.schemas import Work
from scripts.convert_gutenberg_to_storyseek import (
    gutenberg_row_to_storyseek,
    infer_format,
    infer_length_bucket,
    write_jsonl,
)
from scripts.convert_gutenberg_chunks import (
    chunk_row_to_doc,
    clean_chunk_text,
    is_boilerplate_chunk,
)
from scripts.generate_eval_qrels_gutenberg import write_qrels


def _row(book_id: int = 4017) -> dict:
    return {
        "book_id": book_id,
        "title": "The Hollow Needle",
        "author": "Maurice Leblanc",
        "topics": ["Detective and mystery stories", "Fiction"],
        "pg_subjects": ["Burglars -- Fiction", "Lupin, Arsene -- Fiction"],
        "release_date": "May 1, 2003",
        "text": "A burglary has occurred. The detective follows a hidden identity clue.",
    }


def test_gutenberg_row_maps_to_storyseek_work_schema():
    doc = gutenberg_row_to_storyseek(_row())

    work = Work.model_validate(doc)

    assert work.work_id == "pg_4017"
    assert work.creator == "Maurice Leblanc"
    assert work.genres == ["detective and mystery stories", "fiction"]
    assert work.themes == ["burglars -- fiction", "lupin, arsene -- fiction"]
    assert work.tropes == []
    assert work.relationship_dynamics == []
    assert work.content_warnings == ["unknown"]
    assert work.audience_rating == "General"
    assert work.status == "Complete"
    assert work.source == "project_gutenberg"
    assert work.book_id == "4017"
    assert work.pg_subjects == ["burglars -- fiction", "lupin, arsene -- fiction"]
    assert work.topics == ["detective and mystery stories", "fiction"]
    assert work.release_date == "May 1, 2003"


def test_gutenberg_adapter_infers_backend_safe_enums():
    assert infer_format([], ["short stories"], "one two three") == "short_story"
    assert infer_format([], [], "word " * 13_000) == "novel"
    assert infer_length_bucket("word " * 19_999) == "short"
    assert infer_length_bucket("word " * 20_000) == "medium"
    assert infer_length_bucket("word " * 70_000) == "long"


def test_gutenberg_summary_is_excerpt_not_full_text():
    text = "Opening line. " + ("chapter text " * 120)
    doc = gutenberg_row_to_storyseek({**_row(), "text": text})

    assert doc["summary"].startswith("Opening line.")
    assert len(doc["summary"]) < len(text)
    assert doc["summary"].endswith("...")


def test_chunk_cleaning_filters_gutenberg_boilerplate():
    assert is_boilerplate_chunk("The Project Gutenberg eBook. This ebook is for the use of anyone.")
    assert is_boilerplate_chunk("Release date: January 1, 2000 Language: English Credits: Produced by volunteers")
    assert not is_boilerplate_chunk(
        "The detective paused beside the garden gate and saw a dark stain near the stones.",
        min_chars=40,
    )


def test_chunk_row_to_doc_joins_metadata_and_content():
    metadata = gutenberg_row_to_storyseek(_row())
    row = {
        "book_id": 4017,
        "chunk_index": 42,
        "text_chunk": "The detective paused beside the garden gate and saw a dark stain near the stones.",
    }

    doc = chunk_row_to_doc(row, metadata, min_chars=40)

    assert doc is not None
    assert doc["chunk_id"] == "pg_4017_c000042"
    assert doc["work_id"] == "pg_4017"
    assert doc["title"] == "The Hollow Needle"
    assert doc["text_chunk"] == clean_chunk_text(row["text_chunk"])


def test_write_jsonl_skips_duplicate_book_ids(tmp_path):
    out = tmp_path / "works_gutenberg.jsonl"

    count = write_jsonl([_row(1), _row(1), _row(2)], out)
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]

    assert count == 2
    assert [doc["work_id"] for doc in docs] == ["pg_1", "pg_2"]


def test_gutenberg_qrels_grade_topic_and_subject_matches(tmp_path):
    queries = tmp_path / "queries_gutenberg.jsonl"
    works = tmp_path / "works_gutenberg.jsonl"
    qrels = tmp_path / "qrels_gutenberg.csv"
    queries.write_text(
        json.dumps(
            {
                "query_id": "gq_001",
                "query": "detective mystery with burglary",
                "target_topics": ["detective and mystery stories"],
                "target_subject_keywords": ["burglars"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    works.write_text(json.dumps(gutenberg_row_to_storyseek(_row())) + "\n", encoding="utf-8")

    total = write_qrels(queries, works, qrels)

    rows = list(csv.DictReader(qrels.open("r", encoding="utf-8", newline="")))
    assert total == 1
    assert rows == [{"query_id": "gq_001", "work_id": "pg_4017", "relevance": "3"}]
