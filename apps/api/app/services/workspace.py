"""Workspace service — business logic for workspace management."""

from __future__ import annotations

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceRole
from app.repositories.project import ProjectRepository
from app.repositories.workspace import WorkspaceRepository


class WorkspaceService:
    """Handles workspace management business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.workspace_repo = WorkspaceRepository(session)
        self.project_repo = ProjectRepository(session)

    def _generate_slug(self, name: str) -> str:
        """Generate a URL-friendly slug from a workspace name."""
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
        slug = slug.strip("-")
        if not slug:
            slug = "workspace"
        return slug

    async def list_user_workspaces(self, user: User) -> list[dict]:
        """List all workspaces the user belongs to, with counts."""
        workspaces = await self.workspace_repo.get_user_workspaces(user.id)
        result = []
        for ws in workspaces:
            member_count = await self.workspace_repo.get_member_count(ws.id)
            project_count = await self.project_repo.get_workspace_project_count(ws.id)
            result.append({
                "workspace": ws,
                "member_count": member_count,
                "project_count": project_count,
            })
        return result

    async def create_workspace(
        self, user: User, name: str, description: str | None = None
    ) -> Workspace:
        """Create a new workspace."""
        slug = self._generate_slug(name)

        # Check slug uniqueness for this user
        base_slug = slug
        counter = 1
        while await self.workspace_repo.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = await self.workspace_repo.create(
            owner_id=user.id,
            name=name,
            slug=slug,
            description=description,
        )
        return workspace

    async def get_workspace(self, workspace_id: uuid.UUID, user: User) -> Workspace:
        """Get a workspace by ID, verifying the user is a member."""
        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException("Workspace")

        is_member = await self.workspace_repo.is_member(workspace.id, user.id)
        if not is_member:
            raise ForbiddenException("You are not a member of this workspace")

        return workspace

    async def update_workspace(
        self,
        workspace_id: uuid.UUID,
        user: User,
        name: str | None = None,
        description: str | None = None,
    ) -> Workspace:
        """Update a workspace. Only owner and admin can update."""
        workspace = await self.get_workspace(workspace_id, user)

        role = await self.workspace_repo.get_member_role(workspace.id, user.id)
        if role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise ForbiddenException("Only owners and admins can update workspaces")

        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description

        if updates:
            workspace = await self.workspace_repo.update(workspace, **updates)

        return workspace

    async def delete_workspace(self, workspace_id: uuid.UUID, user: User) -> None:
        """Delete a workspace. Only the owner can delete."""
        workspace = await self.get_workspace(workspace_id, user)

        if workspace.owner_id != user.id:
            raise ForbiddenException("Only the workspace owner can delete it")

        await self.workspace_repo.delete(workspace)
