"""Memory-related database models.

TODO: Implement the following models:
- MemoryEntry: Individual memory items
- MemoryCluster: Grouped related memories
- MemoryTag: Tags for categorizing memories
"""

from app.models.base import Base


class MemoryEntry(Base):
    """Individual memory entry stored in the system."""

    __tablename__ = "memory_entries"

    # TODO: Add columns
    # id: Mapped[uuid.UUID]
    # user_id: Mapped[uuid.UUID]
    # content: Mapped[str]
    # memory_type: Mapped[str]  # episodic, semantic, procedural
    # embedding_id: Mapped[str | None]
    # metadata_json: Mapped[dict | None]
    # created_at: Mapped[datetime]
    # updated_at: Mapped[datetime]
    # last_accessed_at: Mapped[datetime | None]
    # importance_score: Mapped[float]
    # access_count: Mapped[int]

    pass


class MemoryCluster(Base):
    """Cluster of related memories."""

    __tablename__ = "memory_clusters"

    # TODO: Add columns
    pass
