"""Memory endpoints — CRUD, search, similarity, and graph visualization."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.memory import (
    GraphResponse,
    MemoryCreateRequest,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    MemoryUpdateRequest,
    SimilarityRequest,
    SimilarityResponse,
)
from app.services.memory.memory import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


def _memory_to_response(memory) -> dict:
    """Convert a Memory model to a response dict."""
    return {
        "id": memory.id,
        "owner_id": memory.owner_id,
        "workspace_id": memory.workspace_id,
        "project_id": memory.project_id,
        "title": memory.title,
        "content": memory.content,
        "summary": memory.summary,
        "embedding_id": memory.embedding_id,
        "memory_type": memory.memory_type,
        "source": memory.source,
        "source_url": memory.source_url,
        "metadata_json": memory.metadata_json,
        "importance_score": memory.importance_score,
        "confidence": memory.confidence,
        "status": memory.status,
        "access_count": memory.access_count,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at,
        "accessed_at": memory.accessed_at,
        "tags": [t.tag for t in memory.tags] if memory.tags else [],
    }


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: MemoryCreateRequest,
    workspace_id: uuid.UUID = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new memory with embedding and graph node."""
    service = MemoryService(db)
    memory = await service.create_memory(
        user=current_user,
        workspace_id=workspace_id,
        title=body.title,
        content=body.content,
        memory_type=body.memory_type,
        project_id=body.project_id,
        summary=body.summary,
        source=body.source,
        source_url=body.source_url,
        tags=body.tags,
        importance_score=body.importance_score,
        confidence=body.confidence,
        metadata_json=body.metadata_json,
        chunking_strategy=body.chunking_strategy,
    )
    await db.commit()
    return _memory_to_response(memory)


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    workspace_id: uuid.UUID = Query(..., description="Workspace ID"),
    project_id: uuid.UUID | None = Query(None, description="Filter by project"),
    memory_type: str | None = Query(None, description="Filter by memory type"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List memories with filtering and pagination."""
    service = MemoryService(db)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    memories, total = await service.list_memories(
        workspace_id=workspace_id,
        user=current_user,
        project_id=project_id,
        memory_type=memory_type,
        tags=tag_list,
        page=page,
        page_size=page_size,
    )
    return {
        "memories": [_memory_to_response(m) for m in memories],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/recent", response_model=list[MemoryResponse])
async def get_recent_memories(
    workspace_id: uuid.UUID = Query(..., description="Workspace ID"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get recently created memories."""
    service = MemoryService(db)
    memories = await service.get_recent(workspace_id, current_user, limit)
    return [_memory_to_response(m) for m in memories]


@router.get("/important", response_model=list[MemoryResponse])
async def get_important_memories(
    workspace_id: uuid.UUID = Query(..., description="Workspace ID"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get the most important memories."""
    service = MemoryService(db)
    memories = await service.get_important(workspace_id, current_user, limit)
    return [_memory_to_response(m) for m in memories]


@router.get("/project/{project_id}", response_model=list[MemoryResponse])
async def get_project_memories(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all memories for a specific project."""
    service = MemoryService(db)
    # We need workspace_id for access check, get it from first memory
    memories, _ = await service.list_memories(
        workspace_id=uuid.UUID(int=0),  # placeholder
        user=current_user,
        project_id=project_id,
        page=1,
        page_size=1000,
    )
    return [_memory_to_response(m) for m in memories]


@router.get("/graph", response_model=GraphResponse)
async def get_memory_graph(
    workspace_id: uuid.UUID = Query(..., description="Workspace ID"),
    project_id: uuid.UUID | None = Query(None, description="Filter by project"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get graph data for memory visualization."""
    service = MemoryService(db)
    graph_data = await service.get_graph(workspace_id, current_user, project_id)
    return graph_data


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific memory by ID."""
    service = MemoryService(db)
    memory = await service.get_memory(memory_id, current_user)
    return _memory_to_response(memory)


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    body: MemoryUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a memory."""
    service = MemoryService(db)
    memory = await service.update_memory(
        memory_id=memory_id,
        user=current_user,
        title=body.title,
        content=body.content,
        summary=body.summary,
        importance_score=body.importance_score,
        confidence=body.confidence,
        status=body.status,
        tags=body.tags,
        metadata_json=body.metadata_json,
    )
    await db.commit()
    return _memory_to_response(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete a memory."""
    service = MemoryService(db)
    await service.delete_memory(memory_id, current_user)
    await db.commit()


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    body: MemorySearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Semantic search across memories."""
    service = MemoryService(db)
    results = await service.search_memories(
        user=current_user,
        workspace_id=body.workspace_id,
        query=body.query,
        project_id=body.project_id,
        memory_type=body.memory_type,
        tags=body.tags,
        top_k=body.top_k,
        min_importance=body.min_importance,
    )
    return {
        "results": [
            MemorySearchResult(
                memory=_memory_to_response(r["memory"]),
                score=r["score"],
                chunk_content=r.get("chunk_content"),
            )
            for r in results
        ],
        "query": body.query,
        "total": len(results),
    }


@router.post("/similarity", response_model=SimilarityResponse)
async def find_similar(
    body: SimilarityRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Find memories similar to a given memory."""
    service = MemoryService(db)
    result = await service.find_similar(
        memory_id=body.memory_id,
        user=current_user,
        top_k=body.top_k,
    )
    return {
        "source_memory": _memory_to_response(result["source_memory"]),
        "similar_memories": [
            MemorySearchResult(
                memory=_memory_to_response(r["memory"]),
                score=r["score"],
                chunk_content=r.get("chunk_content"),
            )
            for r in result["similar_memories"]
        ],
    }
