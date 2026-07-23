"""Embedding service — generates vector embeddings via Ollama.

Abstracts the embedding provider behind a clean interface.
Supports caching to avoid redundant API calls.
"""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = get_logger = structlog.get_logger("synapseos.embeddings")


class EmbeddingService:
    """Generates embeddings using Ollama-compatible models.

    Uses a simple in-memory cache (extendable to Redis).
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        dimensions: int = 768,
    ):
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_host
        self.dimensions = dimensions
        self._cache: dict[str, list[float]] = {}

    def _cache_key(self, text: str) -> str:
        """Generate a cache key from text content."""
        return hashlib.sha256(f"{self.model}:{text}".encode()).hexdigest()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        embedding = await self._call_ollama(text)
        self._cache[cache_key] = embedding
        return embedding

    async def batch_generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        results: list[list[float]] = []
        uncached_texts: list[tuple[int, str]] = []

        # Check cache first
        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                results.append(self._cache[cache_key])
            else:
                results.append([])  # placeholder
                uncached_texts.append((i, text))

        # Generate uncached embeddings
        for idx, text in uncached_texts:
            embedding = await self._call_ollama(text)
            cache_key = self._cache_key(text)
            self._cache[cache_key] = embedding
            results[idx] = embedding

        return results

    async def _call_ollama(self, text: str) -> list[float]:
        """Call Ollama's embedding API."""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding", [])
                if not embedding:
                    raise ValueError("Empty embedding returned from Ollama")
                return embedding
        except httpx.HTTPStatusError as e:
            logger.error("Ollama embedding failed", status=e.response.status_code, error=str(e))
            raise
        except Exception as e:
            logger.error("Ollama embedding error", error=str(e))
            raise

    async def health_check(self) -> dict[str, Any]:
        """Verify the embedding service is reachable."""
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            return {"status": "healthy", "model": self.model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()


# Module-level singleton
embedding_service = EmbeddingService()
