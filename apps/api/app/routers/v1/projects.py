"""Project endpoints — CRUD for projects within a workspace."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: uuid.UUID = Query(..., description="Workspace ID to list projects from"),
    include_archived: bool = Query(False, description="Include archived projects"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List all projects in a workspace."""
    service = ProjectService(db)
    projects = await service.list_projects(
        workspace_id=workspace_id,
        user=current_user,
        include_archived=include_archived,
    )
    return [p.__dict__ for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreateRequest,
    workspace_id: uuid.UUID = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new project in a workspace."""
    service = ProjectService(db)
    project = await service.create_project(
        workspace_id=workspace_id,
        user=current_user,
        name=body.name,
        description=body.description,
        icon=body.icon,
        color=body.color,
    )
    return project.__dict__


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific project."""
    service = ProjectService(db)
    project = await service.get_project(project_id, current_user)
    return project.__dict__


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a project."""
    service = ProjectService(db)
    project = await service.update_project(
        project_id=project_id,
        user=current_user,
        name=body.name,
        description=body.description,
        icon=body.icon,
        color=body.color,
        archived=body.archived,
    )
    return project.__dict__


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project."""
    service = ProjectService(db)
    await service.delete_project(project_id, current_user)
