"""API v1 router — aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from app.routers.v1.auth import router as auth_router
from app.routers.v1.projects import router as projects_router
from app.routers.v1.users import router as users_router
from app.routers.v1.workspaces import router as workspaces_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(workspaces_router)
router.include_router(projects_router)
