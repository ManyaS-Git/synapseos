"""User request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    avatar_url: str | None
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile."""

    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=500)
