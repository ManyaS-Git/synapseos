"""Vector storage service — Qdrant integration with resilient in-memory fallback.

Provides:
- Collection management
- Vector insert/update/delete
- Similarity search with metadata filtering
- High-fidelity cosine similarity fallback when Qdrant is offline
"""

from __future__ import annotations

import math
import uuid
from typing import Any

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


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


class VectorStore:
    """Manages vector storage in Qdrant with local fallback."""

    # Shared memory storage across instances when Qdrant is offline
    _memory_vectors: dict[str, dict[str, Any]] = {}

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
            logger.debug("Could not connect to Qdrant collection, using in-memory store", error=str(e))

    async def insert(
        self,
        vector_id: str,
        embedding: list[float],
        metadata: dict | None = None,
        payload: dict | None = None,
    ) -> None:
        """Insert a single vector with metadata or payload."""
        p = payload if payload is not None else (metadata or {})
        # Always maintain in memory store for instant fallback
        self._memory_vectors[vector_id] = {
            "id": vector_id,
            "vector": embedding,
            "payload": p,
        }

        try:
            point = PointStruct(id=vector_id, vector=embedding, payload=p)
            await self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[point],
            )
        except Exception as e:
            logger.debug("Saved vector to local store (Qdrant unreachable)", id=vector_id, error=str(e))

    async def batch_insert(
        self,
        vectors: list[dict],
    ) -> None:
        """Insert multiple vectors."""
        for v in vectors:
            self._memory_vectors[v["id"]] = {
                "id": v["id"],
                "vector": v["vector"],
                "payload": v.get("payload", {}),
            }

        try:
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
        except Exception as e:
            logger.debug("Batch saved to local store (Qdrant unreachable)", count=len(vectors), error=str(e))

    async def update(
        self,
        vector_id: str,
        embedding: list[float] | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Update a vector's embedding and/or metadata."""
        existing = self._memory_vectors.get(vector_id, {})
        new_vec = embedding if embedding is not None else existing.get("vector", [])
        new_payload = metadata if metadata is not None else existing.get("payload", {})
        self._memory_vectors[vector_id] = {
            "id": vector_id,
            "vector": new_vec,
            "payload": new_payload,
        }

        try:
            if embedding is not None and metadata is not None:
                point = PointStruct(id=vector_id, vector=embedding, payload=metadata)
                await self.client.upsert(collection_name=COLLECTION_NAME, points=[point])
            elif metadata is not None:
                q_existing = await self.get(vector_id)
                if q_existing:
                    point = PointStruct(
                        id=vector_id,
                        vector=q_existing.get("vector", []),
                        payload=metadata,
                    )
                    await self.client.upsert(collection_name=COLLECTION_NAME, points=[point])
        except Exception as e:
            logger.debug("Updated vector in local store", id=vector_id, error=str(e))

    async def delete(self, vector_id: str) -> None:
        """Delete a single vector."""
        self._memory_vectors.pop(vector_id, None)
        try:
            await self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=PointIdsList(points=[vector_id]),
            )
        except Exception:
            pass

    async def batch_delete(self, vector_ids: list[str]) -> None:
        """Delete multiple vectors."""
        for vid in vector_ids:
            self._memory_vectors.pop(vid, None)
        try:
            if vector_ids:
                await self.client.delete(
                    collection_name=COLLECTION_NAME,
                    points_selector=PointIdsList(points=vector_ids),
                )
        except Exception:
            pass

    async def get(self, vector_id: str) -> dict | None:
        """Retrieve a vector by ID."""
        try:
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
        except Exception:
            pass

        return self._memory_vectors.get(vector_id)

    async def search(
        self,
        embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors with optional metadata filtering."""
        try:
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

            if results:
                return [
                    {
                        "id": str(hit.id),
                        "score": hit.score,
                        "payload": hit.payload,
                    }
                    for hit in results
                ]
        except Exception as e:
            logger.debug("Qdrant search unavailable, using local vector search", error=str(e))

        # In-memory cosine search fallback
        scored = []
        for vid, entry in self._memory_vectors.items():
            payload = entry.get("payload", {})
            # Match filters
            if filters:
                match = True
                for k, v in filters.items():
                    if payload.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            score = _cosine_similarity(embedding, entry.get("vector", []))
            scored.append({
                "id": vid,
                "score": round(score, 4),
                "payload": payload,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def count(self) -> int:
        """Count total vectors in the collection."""
        try:
            info = await self.client.get_collection(COLLECTION_NAME)
            if info.points_count is not None:
                return info.points_count
        except Exception:
            pass
        return len(self._memory_vectors)
