from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "storyseek_works"
    opensearch_username: str | None = None
    opensearch_password: str | None = None

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    backend_url: str = "http://localhost:8000"

    data_path: Path = (
        Path(__file__).resolve().parents[2] / "data" / "sample" / "works.jsonl"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
