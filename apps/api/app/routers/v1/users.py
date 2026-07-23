"""User endpoints — profile management."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current user's profile."""
    service = UserService(db)
    return await service.get_profile(current_user.id)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the current user's profile."""
    service = UserService(db)
    return await service.update_profile(
        user=current_user,
        full_name=body.full_name,
        avatar_url=body.avatar_url,
    )
