"""Project repository — data access layer for Project model."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    """CRUD operations for the Project model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        """Fetch a project by ID."""
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_workspace_projects(
        self, workspace_id: uuid.UUID, include_archived: bool = False
    ) -> list[Project]:
        """Get all projects in a workspace."""
        query = select(Project).where(Project.workspace_id == workspace_id)
        if not include_archived:
            query = query.where(Project.archived == False)  # noqa: E712
        query = query.order_by(Project.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: uuid.UUID,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Project:
        """Create a new project."""
        project = Project(
            workspace_id=workspace_id,
            name=name,
            description=description,
            icon=icon,
            color=color,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def update(self, project: Project, **kwargs) -> Project:
        """Update project fields."""
        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        """Delete a project."""
        await self.session.delete(project)
        await self.session.flush()

    async def get_workspace_project_count(self, workspace_id: uuid.UUID) -> int:
        """Count projects in a workspace."""
        result = await self.session.execute(
            select(func.count(Project.id)).where(Project.workspace_id == workspace_id)
        )
        return result.scalar() or 0

    async def name_exists_in_workspace(self, name: str, workspace_id: uuid.UUID) -> bool:
        """Check if a project name already exists in a workspace."""
        result = await self.session.execute(
            select(Project.id).where(
                Project.name == name,
                Project.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none() is not None
