"""Memory service — orchestrates memory CRUD, chunking, embedding, and graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.memory import Memory, MemoryStatus, MemoryType, RelationType
from app.models.user import User
from app.repositories.memory import MemoryRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.memory.chunking import ChunkingService
from app.services.memory.embedding import embedding_service
from app.services.memory.graph import GraphService
from app.services.memory.vector_store import VectorStore

logger = structlog.get_logger("synapseos.memory")

VALID_MEMORY_TYPES = {t.value for t in MemoryType}


class MemoryService:
    """Handles memory management business logic.

    Orchestrates:
    - PostgreSQL (structured metadata)
    - Qdrant (vector embeddings)
    - Neo4j (relationship graph)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.workspace_repo = WorkspaceRepository(session)
        self.chunking = ChunkingService()
        self.vector_store = VectorStore()
        self.graph = GraphService()

    async def _verify_workspace_access(
        self, workspace_id: uuid.UUID, user: User
    ) -> None:
        """Verify the user is a member of the workspace."""
        is_member = await self.workspace_repo.is_member(workspace_id, user.id)
        if not is_member:
            raise ForbiddenException("You are not a member of this workspace")

    async def create_memory(
        self,
        user: User,
        workspace_id: uuid.UUID,
        title: str,
        content: str,
        memory_type: str,
        project_id: uuid.UUID | None = None,
        summary: str | None = None,
        source: str | None = None,
        source_url: str | None = None,
        tags: list[str] | None = None,
        importance_score: float = 0.5,
        confidence: float = 1.0,
        metadata_json: dict | None = None,
        chunking_strategy: str = "recursive",
    ) -> Memory:
        """Create a new memory with embedding and graph node."""
        await self._verify_workspace_access(workspace_id, user)

        if memory_type not in VALID_MEMORY_TYPES:
            raise ValidationException(
                f"Invalid memory type: {memory_type}. Must be one of: {', '.join(VALID_MEMORY_TYPES)}"
            )

        # Create memory in PostgreSQL
        memory = await self.memory_repo.create(
            owner_id=user.id,
            workspace_id=workspace_id,
            project_id=project_id,
            title=title,
            content=content,
            memory_type=memory_type,
            summary=summary,
            source=source,
            source_url=source_url,
            metadata_json=metadata_json,
            importance_score=importance_score,
            confidence=confidence,
            tags=tags,
        )

        # Chunk content
        chunks = self.chunking.chunk(content, chunking_strategy)

        # Generate embeddings and store in Qdrant
        try:
            for chunk in chunks:
                embedding = await embedding_service.generate_embedding(chunk.content)
                embedding_id = f"mem_{memory.id}_chunk_{chunk.index}"
                await self.vector_store.insert(
                    vector_id=embedding_id,
                    embedding=embedding,
                    payload={
                        "memory_id": str(memory.id),
                        "workspace_id": str(workspace_id),
                        "project_id": str(project_id) if project_id else None,
                        "chunk_index": chunk.index,
                        "content": chunk.content,
                        "memory_type": memory_type,
                    },
                )

            # Update memory with primary embedding_id
            primary_embedding_id = f"mem_{memory.id}_chunk_0"
            memory.embedding_id = primary_embedding_id
            await self.session.flush()
        except Exception as e:
            logger.warning("Embedding generation failed, memory saved without vector", error=str(e))

        # Create graph node in Neo4j
        try:
            await self.graph.create_node(
                node_id=str(memory.id),
                label="Memory",
                properties={
                    "title": title,
                    "memory_type": memory_type,
                    "workspace_id": str(workspace_id),
                    "project_id": str(project_id) if project_id else None,
                    "importance_score": importance_score,
                },
            )

            # Create project relationship if applicable
            if project_id:
                await self.graph.create_relationship(
                    source_id=str(memory.id),
                    target_id=str(project_id),
                    relationship_type="BELONGS_TO",
                )
        except Exception as e:
            logger.warning("Graph creation failed, memory saved without graph node", error=str(e))

        return memory

    async def get_memory(self, memory_id: uuid.UUID, user: User) -> Memory:
        """Get a memory by ID, verifying workspace access."""
        memory = await self.memory_repo.get_by_id(memory_id)
        if memory is None or memory.status == MemoryStatus.DELETED:
            raise NotFoundException("Memory")

        await self._verify_workspace_access(memory.workspace_id, user)

        # Increment access count
        await self.memory_repo.increment_access(memory)

        return memory

    async def update_memory(
        self,
        memory_id: uuid.UUID,
        user: User,
        title: str | None = None,
        content: str | None = None,
        summary: str | None = None,
        importance_score: float | None = None,
        confidence: float | None = None,
        status: str | None = None,
        tags: list[str] | None = None,
        metadata_json: dict | None = None,
    ) -> Memory:
        """Update a memory."""
        memory = await self.get_memory(memory_id, user)

        updates = {}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
            # Re-embed if content changed
            try:
                chunks = self.chunking.chunk(content)
                for chunk in chunks:
                    embedding = await embedding_service.generate_embedding(chunk.content)
                    embedding_id = f"mem_{memory.id}_chunk_{chunk.index}"
                    await self.vector_store.update(
                        vector_id=embedding_id,
                        embedding=embedding,
                        payload={
                            "memory_id": str(memory.id),
                            "workspace_id": str(memory.workspace_id),
                            "project_id": str(memory.project_id) if memory.project_id else None,
                            "chunk_index": chunk.index,
                            "content": chunk.content,
                            "memory_type": memory.memory_type,
                        },
                    )
            except Exception as e:
                logger.warning("Re-embedding failed", error=str(e))

        if summary is not None:
            updates["summary"] = summary
        if importance_score is not None:
            updates["importance_score"] = importance_score
        if confidence is not None:
            updates["confidence"] = confidence
        if status is not None:
            updates["status"] = status
        if metadata_json is not None:
            updates["metadata_json"] = metadata_json

        if updates:
            memory = await self.memory_repo.update(memory, **updates)

        if tags is not None:
            memory = await self.memory_repo.update_tags(memory, tags)

        # Update graph node
        try:
            graph_updates = {}
            if title is not None:
                graph_updates["title"] = title
            if importance_score is not None:
                graph_updates["importance_score"] = importance_score
            if graph_updates:
                await self.graph.update_node(
                    node_id=str(memory.id),
                    label="Memory",
                    properties=graph_updates,
                )
        except Exception as e:
            logger.warning("Graph update failed", error=str(e))

        return memory

    async def delete_memory(self, memory_id: uuid.UUID, user: User) -> None:
        """Soft delete a memory and remove from vector store/graph."""
        memory = await self.get_memory(memory_id, user)

        # Soft delete in PostgreSQL
        await self.memory_repo.delete(memory)

        # Delete from Qdrant
        try:
            if memory.embedding_id:
                # Delete all chunks
                chunk_ids = [f"mem_{memory.id}_chunk_{i}" for i in range(20)]  # reasonable max
                await self.vector_store.batch_delete(chunk_ids)
        except Exception as e:
            logger.warning("Vector deletion failed", error=str(e))

        # Delete from Neo4j
        try:
            await self.graph.delete_node(str(memory.id))
        except Exception as e:
            logger.warning("Graph deletion failed", error=str(e))

    async def search_memories(
        self,
        user: User,
        workspace_id: uuid.UUID,
        query: str,
        project_id: uuid.UUID | None = None,
        memory_type: str | None = None,
        tags: list[str] | None = None,
        top_k: int = 10,
        min_importance: float | None = None,
    ) -> list[dict]:
        """Semantic search across memories."""
        await self._verify_workspace_access(workspace_id, user)

        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)

        # Build Qdrant filters
        filters = {"workspace_id": str(workspace_id)}
        if project_id:
            filters["project_id"] = str(project_id)
        if memory_type:
            filters["memory_type"] = memory_type

        # Search Qdrant
        results = await self.vector_store.search(
            embedding=query_embedding,
            top_k=top_k * 2,  # over-fetch for post-filtering
            filters=filters,
        )

        # Post-filter by tags and importance
        filtered_results = []
        for result in results:
            payload = result.get("payload", {})

            # Filter by importance
            if min_importance is not None:
                # We need to get the actual memory to check importance
                memory_id = payload.get("memory_id")
                if memory_id:
                    memory = await self.memory_repo.get_by_id(uuid.UUID(memory_id))
                    if memory and memory.importance_score < min_importance:
                        continue

            filtered_results.append(result)
            if len(filtered_results) >= top_k:
                break

        # Fetch full memory data for results
        search_results = []
        for result in filtered_results:
            memory_id = result.get("payload", {}).get("memory_id")
            if memory_id:
                memory = await self.memory_repo.get_by_id(uuid.UUID(memory_id))
                if memory and memory.status == MemoryStatus.ACTIVE:
                    # Filter by tags if specified
                    if tags:
                        memory_tags = {t.tag for t in memory.tags}
                        if not set(tags).intersection(memory_tags):
                            continue

                    search_results.append({
                        "memory": memory,
                        "score": result.get("score", 0.0),
                        "chunk_content": result.get("payload", {}).get("content"),
                    })

        return search_results[:top_k]

    async def find_similar(
        self,
        memory_id: uuid.UUID,
        user: User,
        top_k: int = 5,
    ) -> dict:
        """Find memories similar to a given memory."""
        memory = await self.get_memory(memory_id, user)

        if not memory.embedding_id:
            raise ValidationException("Memory has no embedding for similarity search")

        # Get the memory's embedding from Qdrant
        source_vector = await self.vector_store.get(memory.embedding_id)
        if not source_vector or not source_vector.get("vector"):
            raise ValidationException("Could not retrieve embedding for similarity search")

        # Search for similar vectors
        results = await self.vector_store.search(
            embedding=source_vector["vector"],
            top_k=top_k + 1,  # +1 to exclude self
            filters={"workspace_id": str(memory.workspace_id)},
        )

        # Build results, excluding the source memory
        similar = []
        for result in results:
            rid = result.get("payload", {}).get("memory_id")
            if rid and rid != str(memory.id):
                rm = await self.memory_repo.get_by_id(uuid.UUID(rid))
                if rm and rm.status == MemoryStatus.ACTIVE:
                    similar.append({
                        "memory": rm,
                        "score": result.get("score", 0.0),
                        "chunk_content": result.get("payload", {}).get("content"),
                    })

        return {
            "source_memory": memory,
            "similar_memories": similar[:top_k],
        }

    async def get_recent(
        self,
        workspace_id: uuid.UUID,
        user: User,
        limit: int = 10,
    ) -> list[Memory]:
        """Get recently created memories."""
        await self._verify_workspace_access(workspace_id, user)
        return await self.memory_repo.get_recent(workspace_id, limit)

    async def get_important(
        self,
        workspace_id: uuid.UUID,
        user: User,
        limit: int = 10,
    ) -> list[Memory]:
        """Get the most important memories."""
        await self._verify_workspace_access(workspace_id, user)
        return await self.memory_repo.get_important(workspace_id, limit)

    async def list_memories(
        self,
        workspace_id: uuid.UUID,
        user: User,
        project_id: uuid.UUID | None = None,
        memory_type: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Memory], int]:
        """List memories with filtering and pagination."""
        await self._verify_workspace_access(workspace_id, user)
        return await self.memory_repo.list_workspace_memories(
            workspace_id=workspace_id,
            project_id=project_id,
            memory_type=memory_type,
            tags=tags,
            page=page,
            page_size=page_size,
        )

    async def get_graph(
        self,
        workspace_id: uuid.UUID,
        user: User,
        project_id: uuid.UUID | None = None,
    ) -> dict:
        """Get graph data for visualization."""
        await self._verify_workspace_access(workspace_id, user)

        try:
            return await self.graph.get_graph_data(
                workspace_id=str(workspace_id),
                project_id=str(project_id) if project_id else None,
            )
        except Exception as e:
            logger.warning("Graph query failed", error=str(e))
            return {"nodes": [], "edges": []}
