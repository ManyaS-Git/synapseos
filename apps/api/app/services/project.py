"""Project service — business logic for project management."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.models.project import Project
from app.repositories.project import ProjectRepository
from app.repositories.workspace import WorkspaceRepository


class ProjectService:
    """Handles project management business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.workspace_repo = WorkspaceRepository(session)

    async def _verify_workspace_access(
        self, workspace_id: uuid.UUID, user: User
    ) -> None:
        """Verify the user is a member of the workspace."""
        is_member = await self.workspace_repo.is_member(workspace_id, user.id)
        if not is_member:
            raise ForbiddenException("You are not a member of this workspace")

    async def list_projects(
        self, workspace_id: uuid.UUID, user: User, include_archived: bool = False
    ) -> list[Project]:
        """List all projects in a workspace."""
        await self._verify_workspace_access(workspace_id, user)
        return await self.project_repo.get_workspace_projects(
            workspace_id, include_archived=include_archived
        )

    async def create_project(
        self,
        workspace_id: uuid.UUID,
        user: User,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Project:
        """Create a new project in a workspace."""
        await self._verify_workspace_access(workspace_id, user)

        # Check name uniqueness within workspace
        if await self.project_repo.name_exists_in_workspace(name, workspace_id):
            raise ValidationException("A project with this name already exists in this workspace")

        project = await self.project_repo.create(
            workspace_id=workspace_id,
            name=name,
            description=description,
            icon=icon,
            color=color,
        )
        return project

    async def get_project(self, project_id: uuid.UUID, user: User) -> Project:
        """Get a project by ID, verifying workspace membership."""
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundException("Project")

        await self._verify_workspace_access(project.workspace_id, user)
        return project

    async def update_project(
        self,
        project_id: uuid.UUID,
        user: User,
        name: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        archived: bool | None = None,
    ) -> Project:
        """Update a project."""
        project = await self.get_project(project_id, user)

        updates = {}
        if name is not None:
            # Check name uniqueness if changing
            if name != project.name:
                if await self.project_repo.name_exists_in_workspace(
                    name, project.workspace_id
                ):
                    raise ValidationException(
                        "A project with this name already exists in this workspace"
                    )
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if icon is not None:
            updates["icon"] = icon
        if color is not None:
            updates["color"] = color
        if archived is not None:
            updates["archived"] = archived

        if updates:
            project = await self.project_repo.update(project, **updates)

        return project

    async def delete_project(self, project_id: uuid.UUID, user: User) -> None:
        """Delete a project."""
        project = await self.get_project(project_id, user)
        await self.project_repo.delete(project)
