"""SynapseOS FastAPI Application Entry Point.

Creates and configures the FastAPI application with:
- Centralized logging setup
- Database connection managers
- Health check endpoints
- CORS middleware
- Request logging
- Graceful startup/shutdown
"""

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import neo4j_manager, postgres, qdrant_manager, redis_manager
from app.core.logging import (
    register_error_handlers,
    setup_logging,
    setup_middleware,
)
from app.core.ollama import ollama_manager
from app.routers.health import router as health_router

logger = structlog.get_logger("synapseos.app")

APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle.

    Startup:
        1. Initialize structured logging
        2. Connect to PostgreSQL
        3. Connect to Redis
        4. Connect to Neo4j
        5. Connect to Qdrant
        6. Print startup summary

    Shutdown:
        1. Disconnect Qdrant
        2. Disconnect Neo4j
        3. Disconnect Redis
        4. Disconnect PostgreSQL
    """
    start_time = time.perf_counter()

    # ── Logging ──────────────────────────────────────────────────────
    setup_logging(
        log_level=settings.app_log_level,
        log_format=settings.log_format,
        log_file=settings.log_file if settings.is_production else None,
        log_max_bytes=settings.log_max_bytes,
        log_backup_count=settings.log_backup_count,
    )

    logger.info(
        "Starting SynapseOS API",
        version=APP_VERSION,
        env=settings.app_env.value,
        debug=settings.app_debug,
    )

    # ── Database connections ─────────────────────────────────────────
    services_connected: list[str] = []
    services_failed: list[str] = []

    for name, manager in [
        ("PostgreSQL", postgres),
        ("Redis", redis_manager),
        ("Neo4j", neo4j_manager),
        ("Qdrant", qdrant_manager),
    ]:
        try:
            await manager.connect()
            services_connected.append(name)
        except Exception as exc:
            logger.warning("Failed to connect", service=name, error=str(exc))
            services_failed.append(name)

    # ── Startup summary ──────────────────────────────────────────────
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "SynapseOS API started",
        version=APP_VERSION,
        env=settings.app_env.value,
        host="0.0.0.0",
        port=8000,
        docs="/docs",
        services_connected=services_connected,
        services_failed=services_failed,
        startup_ms=round(elapsed_ms, 2),
    )

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Shutting down SynapseOS API")
    for name, manager in [
        ("Qdrant", qdrant_manager),
        ("Neo4j", neo4j_manager),
        ("Redis", redis_manager),
        ("PostgreSQL", postgres),
    ]:
        try:
            await manager.disconnect()
            logger.info("Disconnected", service=name)
        except Exception as exc:
            logger.warning("Error disconnecting", service=name, error=str(exc))

    logger.info("SynapseOS API shutdown complete")


def create_app() -> FastAPI:
    """Application factory: creates and configures the FastAPI app."""
    application = FastAPI(
        title="SynapseOS API",
        description="A Privacy-First AI Operating System — Backend API",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware (CORS, request logging)
    setup_middleware(application)

    # Error handlers
    register_error_handlers(application)

    # Routers
    application.include_router(health_router)

    return application


app = create_app()
