"""Workspace endpoints — CRUD for workspaces."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceResponse]:
    """List all workspaces the current user belongs to."""
    service = WorkspaceService(db)
    workspaces = await service.list_user_workspaces(current_user)
    return [
        WorkspaceResponse(
            id=data["workspace"].id,
            owner_id=data["workspace"].owner_id,
            name=data["workspace"].name,
            slug=data["workspace"].slug,
            description=data["workspace"].description,
            created_at=data["workspace"].created_at,
            updated_at=data["workspace"].updated_at,
            member_count=data["member_count"],
            project_count=data["project_count"],
        )
        for data in workspaces
    ]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """Create a new workspace."""
    service = WorkspaceService(db)
    workspace = await service.create_workspace(
        user=current_user,
        name=body.name,
        description=body.description,
    )
    await db.commit()
    return WorkspaceResponse(
        id=workspace.id,
        owner_id=workspace.owner_id,
        name=workspace.name,
        slug=workspace.slug,
        description=workspace.description,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        member_count=1,
        project_count=0,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific workspace."""
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id, current_user)
    return workspace.__dict__


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a workspace."""
    service = WorkspaceService(db)
    workspace = await service.update_workspace(
        workspace_id=workspace_id,
        user=current_user,
        name=body.name,
        description=body.description,
    )
    return workspace.__dict__


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a workspace."""
    service = WorkspaceService(db)
    await service.delete_workspace(workspace_id, current_user)
