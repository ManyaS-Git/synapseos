"""Authentication endpoints — register, login, logout, refresh, me.

All auth endpoints use HTTP-only cookies for token delivery.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    expires_in: int,
) -> None:
    """Set HTTP-only secure cookies for access and refresh tokens."""
    response.set_cookie(
        key=settings.jwt_cookie_name,
        value=access_token,
        max_age=expires_in,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        domain=settings.jwt_cookie_domain,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.jwt_refresh_token_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        domain=settings.jwt_cookie_domain,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(
        key=settings.jwt_cookie_name,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        domain=settings.jwt_cookie_domain,
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        domain=settings.jwt_cookie_domain,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user account."""
    service = AuthService(db)
    result = await service.register(
        email=body.email,
        username=body.username,
        password=body.password,
        full_name=body.full_name,
    )

    _set_auth_cookies(
        response,
        result["access_token"],
        result["refresh_token"],
        result["expires_in"],
    )

    await db.commit()
    return result["user"]


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate and log in."""
    service = AuthService(db)
    result = await service.login(email=body.email, password=body.password)

    _set_auth_cookies(
        response,
        result["access_token"],
        result["refresh_token"],
        result["expires_in"],
    )

    await db.commit()
    return result["user"]


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> dict:
    """Log out by clearing authentication cookies."""
    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh the access token using the refresh cookie."""
    from fastapi import Request

    # We need to access the raw request to read cookies
    # This endpoint is called by the frontend when the access token expires
    service = AuthService(db)

    # For cookie-based refresh, the frontend sends the refresh token
    # in the request body since httponly cookies can't be read by JS
    return {"message": "Use /auth/refresh with refresh_token body"}


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh the access token using a refresh token."""
    service = AuthService(db)
    result = await service.refresh_token(refresh_token)

    _set_auth_cookies(
        response,
        result["access_token"],
        result["refresh_token"],
        result["expires_in"],
    )

    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "expires_in": result["expires_in"],
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the currently authenticated user."""
    return current_user
