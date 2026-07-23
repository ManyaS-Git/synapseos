"""User service — business logic for user management."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    """Handles user management business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_profile(self, user_id: uuid.UUID) -> User:
        """Get a user's profile."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User")
        return user

    async def update_profile(
        self,
        user: User,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Update a user's profile."""
        updates = {}
        if full_name is not None:
            updates["full_name"] = full_name
        if avatar_url is not None:
            updates["avatar_url"] = avatar_url

        if updates:
            user = await self.user_repo.update(user, **updates)

        return user
