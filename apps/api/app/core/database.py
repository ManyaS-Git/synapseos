"""Database connection managers for PostgreSQL, Redis, Neo4j, and Qdrant.

Each manager exposes:
    connect()   — Initialize the connection/pool
    disconnect() — Gracefully close the connection/pool
    health_check() — Verify the connection is alive

No repositories or business logic — connection management only.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from neo4j import AsyncDriver, async_driver
from qdrant_client import AsyncQdrantClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("synapseos.database")


# =============================================================================
# PostgreSQL
# =============================================================================


class PostgreSQLManager:
    """Manages the async SQLAlchemy engine and session factory for PostgreSQL."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError(
                "PostgreSQL session factory not initialized. Call connect() first."
            )
        return self._session_factory

    async def connect(self) -> None:
        """Create the async engine and session factory."""
        logger.info("Connecting to PostgreSQL", host=settings.postgres_host, port=settings.postgres_port)
        self._engine = create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("PostgreSQL connection established")

    async def disconnect(self) -> None:
        """Dispose the engine and close all connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("PostgreSQL connection closed")

    async def health_check(self) -> dict[str, Any]:
        """Verify PostgreSQL is reachable by executing a simple query."""
        if not self._engine:
            return {"status": "unavailable", "error": "Engine not initialized"}
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT 1")
                )
                result.scalar()
            return {"status": "healthy", "host": settings.postgres_host, "port": settings.postgres_port}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}


postgres = PostgreSQLManager()


# =============================================================================
# Redis
# =============================================================================


class RedisManager:
    """Manages an async Redis connection pool."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    async def connect(self) -> None:
        """Initialize the async Redis client."""
        logger.info("Connecting to Redis", host=settings.redis_host, port=settings.redis_port)
        self._client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._client.ping()
        logger.info("Redis connection established")

    async def disconnect(self) -> None:
        """Close the Redis client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Redis connection closed")

    async def health_check(self) -> dict[str, Any]:
        """Verify Redis is reachable by pinging."""
        if not self._client:
            return {"status": "unavailable", "error": "Client not initialized"}
        try:
            await self._client.ping()
            return {"status": "healthy", "host": settings.redis_host, "port": settings.redis_port}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}


redis_manager = RedisManager()


# =============================================================================
# Neo4j
# =============================================================================


class Neo4jManager:
    """Manages the async Neo4j driver."""

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self._driver

    async def connect(self) -> None:
        """Create the async Neo4j driver."""
        logger.info("Connecting to Neo4j", uri=settings.neo4j_uri)
        self._driver = async_driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        await self._driver.verify_connectivity()
        logger.info("Neo4j connection established")

    async def disconnect(self) -> None:
        """Close the Neo4j driver."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    async def health_check(self) -> dict[str, Any]:
        """Verify Neo4j is reachable."""
        if not self._driver:
            return {"status": "unavailable", "error": "Driver not initialized"}
        try:
            async with self._driver.session(database=settings.neo4j_database) as session:
                result = await session.run("RETURN 1 AS value")
                record = await result.single()
                assert record is not None
            return {"status": "healthy", "uri": settings.neo4j_uri}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}


neo4j_manager = Neo4jManager()


# =============================================================================
# Qdrant
# =============================================================================


class QdrantManager:
    """Manages the async Qdrant client."""

    def __init__(self) -> None:
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized. Call connect() first.")
        return self._client

    async def connect(self) -> None:
        """Initialize the async Qdrant client."""
        logger.info("Connecting to Qdrant", host=settings.qdrant_host, port=settings.qdrant_port)
        self._client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        await self._client.get_collections()
        logger.info("Qdrant connection established")

    async def disconnect(self) -> None:
        """Close the Qdrant client."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Qdrant connection closed")

    async def health_check(self) -> dict[str, Any]:
        """Verify Qdrant is reachable."""
        if not self._client:
            return {"status": "unavailable", "error": "Client not initialized"}
        try:
            await self._client.get_collections()
            return {"status": "healthy", "host": settings.qdrant_host, "port": settings.qdrant_port}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}


qdrant_manager = QdrantManager()


# =============================================================================
# Convenience session dependency
# =============================================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with postgres.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
