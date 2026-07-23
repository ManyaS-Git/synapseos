"""Memory-related Pydantic schemas.

TODO: Implement the following schemas:
- MemoryCreate
- MemoryUpdate
- MemoryResponse
- MemoryListResponse
- MemorySearchRequest
"""

from pydantic import BaseModel


class MemoryBase(BaseModel):
    """Base schema for memory operations."""
    pass


# TODO: Implement schemas
# class MemoryCreate(MemoryBase):
#     content: str
#     memory_type: str
#     tags: list[str] = []
#     metadata: dict = {}
#
# class MemoryResponse(MemoryBase):
#     id: uuid.UUID
#     content: str
#     memory_type: str
#     created_at: datetime
#     importance_score: float
#
#     model_config = ConfigDict(from_attributes=True)
