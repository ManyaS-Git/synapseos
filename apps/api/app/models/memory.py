"""Memory system enums and database models.

Implements the hybrid memory architecture:
- Structured Metadata (PostgreSQL)
- Semantic Memory (Qdrant embeddings)
- Relationship Memory (Neo4j graph)
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ── Enums ─────────────────────────────────────────────────────────────────


class MemoryType(str, PyEnum):
    """Types of memories the system supports."""

    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    DOCUMENT = "document"
    TASK = "task"
    PROJECT = "project"
    PREFERENCE = "preference"
    EVENT = "event"
    OBSERVATION = "observation"


class MemoryStatus(str, PyEnum):
    """Lifecycle status of a memory."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChunkingStrategy(str, PyEnum):
    """Strategies for splitting content into chunks."""

    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    RECURSIVE = "recursive"


class RelationType(str, PyEnum):
    """Types of relationships between entities in the knowledge graph."""

    RELATED_TO = "related_to"
    MENTIONED_IN = "mentioned_in"
    PART_OF = "part_of"
    CAUSED_BY = "caused_by"
    FOLLOWS = "follows"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    TAGGED_WITH = "tagged_with"
    BELONGS_TO = "belongs_to"
    CREATED_IN = "created_in"


# ── Models ────────────────────────────────────────────────────────────────


class Memory(Base):
    """Core memory model — stores structured metadata in PostgreSQL.

    Each memory has an embedding stored in Qdrant and may have
    relationships stored in Neo4j.
    """

    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    memory_type: Mapped[MemoryType] = mapped_column(
        String(50), nullable=False, index=True
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[MemoryStatus] = mapped_column(
        String(20), default=MemoryStatus.ACTIVE, nullable=False, index=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    chunks = relationship("MemoryChunk", back_populates="memory", cascade="all, delete-orphan")
    tags = relationship("MemoryTag", back_populates="memory", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Memory {self.title[:50]} ({self.memory_type})>"


class MemoryChunk(Base):
    """Chunked content for embedding and retrieval.

    Large memories are split into chunks for better semantic search.
    Each chunk gets its own embedding in Qdrant.
    """

    __tablename__ = "memory_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    memory = relationship("Memory", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<MemoryChunk index={self.chunk_index}>"


class MemoryTag(Base):
    """Tags for categorizing and filtering memories."""

    __tablename__ = "memory_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    memory = relationship("Memory", back_populates="tags")

    def __repr__(self) -> str:
        return f"<MemoryTag {self.tag}>"


class MemoryRelation(Base):
    """Relationships between memories and other entities.

    Stored in PostgreSQL for fast queries, with a parallel
    representation in Neo4j for graph traversal.
    """

    __tablename__ = "memory_relations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_memory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=True,
    )
    relation_type: Mapped[RelationType] = mapped_column(
        String(50), nullable=False
    )
    target_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MemoryRelation {self.relation_type}>"
