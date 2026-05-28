from __future__ import annotations

from backend.app import chunk_loader


def test_chunk_actions_enrich_docs_with_embedding(monkeypatch):
    monkeypatch.setattr(chunk_loader, "embed_texts", lambda texts: [[0.2] * 384 for _ in texts])
    docs = [
        {
            "chunk_id": "pg_1_c000001",
            "work_id": "pg_1",
            "book_id": "1",
            "chunk_index": 1,
            "title": "A Mystery",
            "creator": "Author",
            "genres": ["detective and mystery stories"],
            "themes": ["gardens -- fiction"],
            "text_chunk": "The detective found blood near the garden gate.",
            "source": "project_gutenberg",
        }
    ]

    actions = list(chunk_loader._actions(docs, "storyseek_chunks"))

    assert actions[0]["_index"] == "storyseek_chunks"
    assert actions[0]["_id"] == "pg_1_c000001"
    source = actions[0]["_source"]
    assert "garden gate" in source["combined_text"]
    assert source["embedding"] == [0.2] * 384
