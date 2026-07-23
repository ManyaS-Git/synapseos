"""Memory request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Memory ────────────────────────────────────────────────────────────────


class MemoryCreateRequest(BaseModel):
    """Schema for creating a memory."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    summary: str | None = Field(None, max_length=2000)
    memory_type: str = Field(..., description="Memory type enum value")
    project_id: uuid.UUID | None = None
    source: str | None = Field(None, max_length=255)
    source_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata_json: dict | None = None
    chunking_strategy: str = Field(
        default="recursive",
        description="Chunking strategy: sentence, paragraph, recursive",
    )


class MemoryUpdateRequest(BaseModel):
    """Schema for updating a memory."""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1)
    summary: str | None = Field(None, max_length=2000)
    importance_score: float | None = Field(None, ge=0.0, le=1.0)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    status: str | None = None
    tags: list[str] | None = None
    metadata_json: dict | None = None


class MemoryResponse(BaseModel):
    """Schema for memory data in API responses."""

    id: uuid.UUID
    owner_id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    content: str
    summary: str | None
    embedding_id: str | None
    memory_type: str
    source: str | None
    source_url: str | None
    metadata_json: dict | None
    importance_score: float
    confidence: float
    status: str
    access_count: int
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime | None
    tags: list[str] = []

    model_config = {"from_attributes": True}


class MemoryListResponse(BaseModel):
    """Paginated memory list response."""

    memories: list[MemoryResponse]
    total: int
    page: int
    page_size: int


# ── Search ────────────────────────────────────────────────────────────────


class MemorySearchRequest(BaseModel):
    """Schema for semantic memory search."""

    query: str = Field(..., min_length=1, max_length=1000)
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    memory_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=100)
    min_importance: float | None = Field(None, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    """A single search result with similarity score."""

    memory: MemoryResponse
    score: float
    chunk_content: str | None = None


class MemorySearchResponse(BaseModel):
    """Search results response."""

    results: list[MemorySearchResult]
    query: str
    total: int


# ── Similarity ────────────────────────────────────────────────────────────


class SimilarityRequest(BaseModel):
    """Schema for finding similar memories."""

    memory_id: uuid.UUID
    top_k: int = Field(default=5, ge=1, le=50)


class SimilarityResponse(BaseModel):
    """Similarity search results."""

    source_memory: MemoryResponse
    similar_memories: list[MemorySearchResult]


# ── Graph ─────────────────────────────────────────────────────────────────


class GraphNodeResponse(BaseModel):
    """A node in the memory graph."""

    id: str
    label: str
    type: str
    memory_type: str | None = None
    metadata: dict | None = None


class GraphEdgeResponse(BaseModel):
    """An edge in the memory graph."""

    id: str
    source: str
    target: str
    label: str
    weight: float = 1.0


class GraphResponse(BaseModel):
    """Full graph response for visualization."""

    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
