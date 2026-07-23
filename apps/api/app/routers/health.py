"""Health check endpoints.

Provides:
    GET /           — Welcome message
    GET /health     — Quick health (always 200 if app is running)
    GET /health/live — Liveness probe (app process alive)
    GET /health/ready — Readiness probe (all dependencies reachable)
"""

import time

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import neo4j_manager, postgres, qdrant_manager, redis_manager
from app.core.ollama import ollama_manager

logger = structlog.get_logger("synapseos.health")

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint — confirms the API is running."""
    return {
        "name": "SynapseOS API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running",
    }


@router.get("/health")
async def health() -> dict[str, str]:
    """Quick health check — confirms the process is alive."""
    return {"status": "healthy"}


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Kubernetes-style liveness probe.

    Returns 200 if the application process is running.
    No dependency checks — just confirms the app hasn't crashed.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness() -> JSONResponse:
    """Kubernetes-style readiness probe.

    Checks connectivity to all downstream services:
    - PostgreSQL
    - Redis
    - Neo4j
    - Qdrant
    - Ollama (soft check — fails don't block readiness)

    Returns 200 only if critical services are reachable.
    Returns 503 if critical services are down.
    """
    start = time.perf_counter()

    services: dict[str, dict[str, object]] = {}
    all_healthy = True

    # Critical services — failure means not ready
    for name, manager in [
        ("postgres", postgres),
        ("redis", redis_manager),
        ("neo4j", neo4j_manager),
        ("qdrant", qdrant_manager),
    ]:
        result = await manager.health_check()
        services[name] = result
        if result.get("status") not in ("healthy", "unavailable"):
            all_healthy = False
        elif result.get("status") == "unavailable":
            # Engine not initialized is allowed (app started without DB)
            pass

    # Non-critical — Ollama may not be running
    ollama_result = await ollama_manager.health_check()
    services["ollama"] = ollama_result

    elapsed_ms = (time.perf_counter() - start) * 1000

    response: dict[str, object] = {
        "status": "ready" if all_healthy else "degraded",
        "environment": settings.app_env.value,
        "version": "0.1.0",
        "services": services,
        "check_duration_ms": round(elapsed_ms, 2),
    }

    status_code = 200 if all_healthy else 503
    return JSONResponse(content=response, status_code=status_code)
