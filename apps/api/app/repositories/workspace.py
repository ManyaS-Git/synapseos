"""Workspace repository — data access layer for Workspace model."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


class WorkspaceRepository:
    """CRUD operations for the Workspace model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        """Fetch a workspace by ID with member count."""
        result = await self.session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Workspace | None:
        """Fetch a workspace by slug."""
        result = await self.session.execute(select(Workspace).where(Workspace.slug == slug))
        return result.scalar_one_or_none()

    async def get_user_workspaces(self, user_id: uuid.UUID) -> list[Workspace]:
        """Get all workspaces where the user is a member."""
        result = await self.session.execute(
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        slug: str,
        description: str | None = None,
    ) -> Workspace:
        """Create a workspace and add the owner as a member."""
        workspace = Workspace(
            owner_id=owner_id,
            name=name,
            slug=slug,
            description=description,
        )
        self.session.add(workspace)
        await self.session.flush()

        # Add owner as a member with OWNER role
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=WorkspaceRole.OWNER,
        )
        self.session.add(member)
        await self.session.flush()

        return workspace

    async def update(self, workspace: Workspace, **kwargs) -> Workspace:
        """Update workspace fields."""
        for key, value in kwargs.items():
            if value is not None and hasattr(workspace, key):
                setattr(workspace, key, value)
        await self.session.flush()
        return workspace

    async def delete(self, workspace: Workspace) -> None:
        """Delete a workspace (cascades to members and projects)."""
        await self.session.delete(workspace)
        await self.session.flush()

    async def slug_exists(self, slug: str) -> bool:
        """Check if a slug is already taken."""
        result = await self.session.execute(select(Workspace.id).where(Workspace.slug == slug))
        return result.scalar_one_or_none() is not None

    async def is_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if a user is a member of a workspace."""
        result = await self.session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_member_role(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkspaceRole | None:
        """Get a user's role in a workspace."""
        result = await self.session.execute(
            select(WorkspaceMember.role).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_member_count(self, workspace_id: uuid.UUID) -> int:
        """Count members in a workspace."""
        result = await self.session.execute(
            select(func.count(WorkspaceMember.user_id)).where(
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        return result.scalar() or 0

    async def slug_exists_for_user(self, slug: str, user_id: uuid.UUID) -> bool:
        """Check if a user already owns a workspace with this slug."""
        result = await self.session.execute(
            select(Workspace.id).where(
                Workspace.slug == slug,
                Workspace.owner_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None
