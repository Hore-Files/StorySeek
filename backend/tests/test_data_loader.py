from __future__ import annotations

from backend.app import data_loader


def test_actions_enrich_docs_with_combined_text_and_embedding(monkeypatch):
    monkeypatch.setattr(data_loader, "embed_texts", lambda texts: [[0.1] * 384 for _ in texts])
    docs = [
        {
            "work_id": "w_0001",
            "title": "Glass Letter",
            "summary": "A slow burn mystery.",
            "genres": ["mystery"],
            "themes": ["healing"],
            "tropes": ["slow burn"],
            "relationship_dynamics": ["rivals"],
        }
    ]

    actions = list(data_loader._actions(docs, "storyseek_works"))

    assert actions[0]["_index"] == "storyseek_works"
    assert actions[0]["_id"] == "w_0001"
    source = actions[0]["_source"]
    assert "Glass Letter" in source["combined_text"]
    assert "slow burn" in source["combined_text"]
    assert source["embedding"] == [0.1] * 384
