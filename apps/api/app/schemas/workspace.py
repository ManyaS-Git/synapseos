"""Workspace request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceCreateRequest(BaseModel):
    """Schema for creating a workspace."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class WorkspaceUpdateRequest(BaseModel):
    """Schema for updating a workspace."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class WorkspaceMemberResponse(BaseModel):
    """Schema for workspace member data."""

    user_id: uuid.UUID
    username: str
    email: str
    full_name: str | None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    """Schema for workspace data in API responses."""

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    project_count: int = 0

    model_config = {"from_attributes": True}
