"""Project request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Schema for creating a project."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ProjectUpdateRequest(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    archived: bool | None = None


class ProjectResponse(BaseModel):
    """Schema for project data in API responses."""

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    icon: str | None
    color: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
