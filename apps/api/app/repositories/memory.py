"""Memory repository — data access layer for Memory model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.memory import Memory, MemoryStatus, MemoryTag, MemoryType


class MemoryRepository:
    """CRUD and query operations for the Memory model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, memory_id: uuid.UUID) -> Memory | None:
        """Fetch a memory by ID with tags."""
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        owner_id: uuid.UUID,
        workspace_id: uuid.UUID,
        title: str,
        content: str,
        memory_type: str,
        project_id: uuid.UUID | None = None,
        summary: str | None = None,
        embedding_id: str | None = None,
        source: str | None = None,
        source_url: str | None = None,
        metadata_json: dict | None = None,
        importance_score: float = 0.5,
        confidence: float = 1.0,
        tags: list[str] | None = None,
    ) -> Memory:
        """Create a new memory with optional tags."""
        memory = Memory(
            owner_id=owner_id,
            workspace_id=workspace_id,
            project_id=project_id,
            title=title,
            content=content,
            summary=summary,
            embedding_id=embedding_id,
            memory_type=memory_type,
            source=source,
            source_url=source_url,
            metadata_json=metadata_json,
            importance_score=importance_score,
            confidence=confidence,
        )
        self.session.add(memory)
        await self.session.flush()

        # Add tags
        if tags:
            for tag_name in tags:
                tag = MemoryTag(memory_id=memory.id, tag=tag_name.lower().strip())
                self.session.add(tag)
            await self.session.flush()

        # Reload with relationships
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory.id)
        )
        return result.scalar_one()

    async def update(self, memory: Memory, **kwargs) -> Memory:
        """Update memory fields."""
        for key, value in kwargs.items():
            if key == "tags":
                continue  # Handle tags separately
            if value is not None and hasattr(memory, key):
                setattr(memory, key, value)
        await self.session.flush()
        return memory

    async def update_tags(self, memory: Memory, tags: list[str]) -> Memory:
        """Replace all tags for a memory."""
        # Delete existing tags
        for tag in memory.tags:
            await self.session.delete(tag)
        await self.session.flush()

        # Add new tags
        for tag_name in tags:
            tag = MemoryTag(memory_id=memory.id, tag=tag_name.lower().strip())
            self.session.add(tag)
        await self.session.flush()

        # Reload
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory.id)
        )
        return result.scalar_one()

    async def delete(self, memory: Memory) -> None:
        """Soft delete a memory."""
        memory.status = MemoryStatus.DELETED
        await self.session.flush()

    async def list_workspace_memories(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
        memory_type: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Memory], int]:
        """List memories in a workspace with filtering and pagination."""
        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.status == MemoryStatus.ACTIVE,
                )
            )
        )

        if project_id:
            query = query.where(Memory.project_id == project_id)

        if memory_type:
            query = query.where(Memory.memory_type == memory_type)

        if tags:
            # Join with tags table for tag filtering
            query = query.join(MemoryTag).where(MemoryTag.tag.in_(tags))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.order_by(Memory.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        memories = list(result.scalars().all())

        return memories, total

    async def get_recent(
        self,
        workspace_id: uuid.UUID,
        limit: int = 10,
    ) -> list[Memory]:
        """Get the most recently created memories."""
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.status == MemoryStatus.ACTIVE,
                )
            )
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_important(
        self,
        workspace_id: uuid.UUID,
        limit: int = 10,
    ) -> list[Memory]:
        """Get the most important memories."""
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.status == MemoryStatus.ACTIVE,
                )
            )
            .order_by(Memory.importance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def increment_access(self, memory: Memory) -> None:
        """Increment the access count and update accessed_at."""
        memory.access_count += 1
        memory.accessed_at = datetime.now(timezone.utc)
        await self.session.flush()
