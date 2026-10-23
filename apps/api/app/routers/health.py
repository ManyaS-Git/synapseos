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
    docs_path = "/docs" if (not settings.is_production or settings.enable_docs_in_production) else "disabled"
    return {
        "name": "SynapseOS API",
        "version": "0.4.0",
        "docs": docs_path,
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

    Checks connectivity to downstream services:
    - Primary database (PostgreSQL or durable SQLite fallback)
    - Redis (cache & message broker)
    - Neo4j (graph database)
    - Qdrant (vector store)
    - Ollama (soft check)
    - Nebius Token Factory

    In local/embedded or auto mode, a healthy primary database and local fallback
    guarantees ready status (HTTP 200). In distributed mode, all critical services
    must be healthy.
    """
    start = time.perf_counter()

    services: dict[str, dict[str, object]] = {}

    for name, manager in [
        ("postgres", postgres),
        ("redis", redis_manager),
        ("neo4j", neo4j_manager),
        ("qdrant", qdrant_manager),
    ]:
        services[name] = await manager.health_check()

    # Soft checks (non-blocking)
    services["ollama"] = await ollama_manager.health_check()

    # Nebius Token Factory provider status
    from app.core.llm.nebius import nebius_client
    services["nebius_token_factory"] = await nebius_client.health_check()

    # Determine readiness based on storage mode
    db_healthy = services["postgres"].get("status") == "healthy"
    any_unhealthy = any(
        s.get("status") == "unhealthy"
        for k, s in services.items()
        if k in ("postgres", "redis", "neo4j", "qdrant")
    )

    if settings.storage_mode == "distributed":
        # Distributed mode requires all 4 core services to be healthy
        is_ready = db_healthy and all(
            services[k].get("status") == "healthy"
            for k in ("postgres", "redis", "neo4j", "qdrant")
        )
    else:
        # local_embedded or auto: primary db must be healthy and no connected service in failure state
        is_ready = db_healthy and not any_unhealthy

    elapsed_ms = (time.perf_counter() - start) * 1000

    response: dict[str, object] = {
        "status": "ready" if is_ready else "degraded",
        "environment": settings.app_env.value,
        "version": "0.4.0",
        "storage_mode": settings.storage_mode,
        "privacy_mode": settings.privacy_mode,
        "services": services,
        "check_duration_ms": round(elapsed_ms, 2),
    }

    status_code = 200 if is_ready else 503
    return JSONResponse(content=response, status_code=status_code)

