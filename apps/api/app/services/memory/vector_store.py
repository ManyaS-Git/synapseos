"""Vector storage service — Qdrant integration for semantic search.

Provides:
- Collection management
- Vector insert/update/delete
- Similarity search with metadata filtering
"""

from __future__ import annotations

import uuid

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

logger = structlog.get_logger("synapseos.vector")

COLLECTION_NAME = "memory_embeddings"


class VectorStore:
    """Manages vector storage in Qdrant for memory embeddings."""

    def __init__(self, client: AsyncQdrantClient | None = None):
        self._client = client
        self._dimensions = 768  # Default for nomic-embed-text

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            from app.core.database import qdrant_manager
            self._client = qdrant_manager.client
        return self._client

    async def ensure_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        try:
            collections = await self.client.get_collections()
            existing = [c.name for c in collections.collections]
            if COLLECTION_NAME not in existing:
                await self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self._dimensions,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection", collection=COLLECTION_NAME)
        except Exception as e:
            logger.warning("Could not ensure Qdrant collection", error=str(e))

    async def insert(
        self,
        vector_id: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Insert a single vector with metadata."""
        payload = metadata or {}
        point = PointStruct(
            id=vector_id,
            vector=embedding,
            payload=payload,
        )
        await self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point],
        )

    async def batch_insert(
        self,
        vectors: list[dict],
    ) -> None:
        """Insert multiple vectors.

        Each dict should have: id, vector, payload (optional).
        """
        points = [
            PointStruct(
                id=v["id"],
                vector=v["vector"],
                payload=v.get("payload", {}),
            )
            for v in vectors
        ]
        await self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

    async def update(
        self,
        vector_id: str,
        embedding: list[float] | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Update a vector's embedding and/or metadata."""
        if embedding is not None and metadata is not None:
            point = PointStruct(id=vector_id, vector=embedding, payload=metadata)
            await self.client.upsert(collection_name=COLLECTION_NAME, points=[point])
        elif metadata is not None:
            # Update payload only (use set_payload if available, otherwise upsert with existing vector)
            # For simplicity, we use a search + upsert pattern
            existing = await self.get(vector_id)
            if existing:
                point = PointStruct(
                    id=vector_id,
                    vector=existing.get("vector", []),
                    payload=metadata,
                )
                await self.client.upsert(collection_name=COLLECTION_NAME, points=[point])

    async def delete(self, vector_id: str) -> None:
        """Delete a single vector."""
        await self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=PointIdsList(points=[vector_id]),
        )

    async def batch_delete(self, vector_ids: list[str]) -> None:
        """Delete multiple vectors."""
        if vector_ids:
            await self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=PointIdsList(points=vector_ids),
            )

    async def get(self, vector_id: str) -> dict | None:
        """Retrieve a vector by ID."""
        results = await self.client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[vector_id],
        )
        if results:
            point = results[0]
            return {
                "id": str(point.id),
                "vector": point.vector,
                "payload": point.payload,
            }
        return None

    async def search(
        self,
        embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors with optional metadata filtering."""
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            if conditions:
                query_filter = Filter(must=conditions)

        results = await self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=top_k,
            query_filter=query_filter,
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    async def count(self) -> int:
        """Count total vectors in the collection."""
        try:
            info = await self.client.get_collection(COLLECTION_NAME)
            return info.points_count or 0
        except Exception:
            return 0
