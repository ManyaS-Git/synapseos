"""User repository — data access layer for User model."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """CRUD operations for the User model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by username."""
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        full_name: str | None = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already taken."""
        result = await self.session.execute(select(User.id).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def username_exists(self, username: str) -> bool:
        """Check if a username is already taken."""
        result = await self.session.execute(select(User.id).where(User.username == username))
        return result.scalar_one_or_none() is not None
