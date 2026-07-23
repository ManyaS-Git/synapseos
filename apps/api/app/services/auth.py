"""Authentication service — registration, login, token management."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    """Handles authentication business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str | None = None,
    ) -> dict:
        """Register a new user. Returns tokens."""
        # Validate email format
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValidationException("Invalid email format")

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            raise ValidationException(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        if len(username) < 3:
            raise ValidationException("Username must be at least 3 characters")

        # Validate password strength
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", password):
            raise ValidationException("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValidationException("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValidationException("Password must contain at least one number")

        # Check uniqueness
        if await self.user_repo.email_exists(email):
            raise ConflictException("Email already registered")
        if await self.user_repo.username_exists(username):
            raise ConflictException("Username already taken")

        # Create user
        user = await self.user_repo.create(
            email=email,
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
        )

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.jwt_access_token_minutes * 60,
        }

    async def login(self, email: str, password: str) -> dict:
        """Authenticate a user. Returns tokens."""
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.session.flush()

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.jwt_access_token_minutes * 60,
        }

    async def refresh_token(self, refresh_token_str: str) -> dict:
        """Refresh an access token using a valid refresh token."""
        payload = decode_token(refresh_token_str)
        if payload is None or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Invalid token payload")

        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.jwt_access_token_minutes * 60,
        }
