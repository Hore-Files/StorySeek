from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Format = Literal["novel", "short_story", "fanfic_style", "manga", "webnovel"]
Status = Literal["Complete", "Ongoing", "Hiatus"]
Length = Literal["short", "medium", "long"]
Audience = Literal["General", "Teen", "Mature"]
# Modes that the backend can serve today.
SearchMode = Literal["bm25", "dense", "hybrid"]


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
    book_id: str | None = None
    pg_subjects: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    release_date: str | None = None


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


class MatchedPassage(BaseModel):
    chunk_id: str
    chunk_index: int
    text_chunk: str
    score: float


class SearchHit(BaseModel):
    work: Work
    score: float
    explanation: list[str] = Field(default_factory=list)
    matched_passages: list[MatchedPassage] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    total: int
    page: int
    size: int
    hits: list[SearchHit]


class FacetResponse(BaseModel):
    formats: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    tropes: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    length_buckets: list[str] = Field(default_factory=list)
    audience_ratings: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    content_warnings: list[str] = Field(default_factory=list)
