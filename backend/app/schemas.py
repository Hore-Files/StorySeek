from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Format = Literal["novel", "short_story", "fanfic_style", "manga", "webnovel"]
Status = Literal["Complete", "Ongoing", "Hiatus"]
Length = Literal["short", "medium", "long"]
Audience = Literal["General", "Teen", "Mature"]
# Modes that the backend can actually serve today. Dense and hybrid are
# documented in docs/architecture.md as planned; they are not part of the
# request contract so the OpenAPI schema stays honest.
SearchMode = Literal["bm25"]


class Work(BaseModel):
    work_id: str
    title: str
    creator: str
    format: Format
    summary: str
    genres: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    tropes: list[str] = Field(default_factory=list)
    relationship_dynamics: list[str] = Field(default_factory=list)
    content_warnings: list[str] = Field(default_factory=list)
    audience_rating: Audience
    status: Status
    length_bucket: Length
    language: str = "English"
    source: str = "synthetic"


class SearchFilters(BaseModel):
    formats: list[Format] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    tropes: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    statuses: list[Status] = Field(default_factory=list)
    length_buckets: list[Length] = Field(default_factory=list)
    audience_ratings: list[Audience] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = ""
    filters: SearchFilters = Field(default_factory=SearchFilters)
    exclude_warnings: list[str] = Field(default_factory=list)
    mode: SearchMode = "bm25"
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=50)


class SearchHit(BaseModel):
    work: Work
    score: float
    explanation: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    total: int
    page: int
    size: int
    hits: list[SearchHit]
