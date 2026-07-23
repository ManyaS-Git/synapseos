"""Ollama connectivity manager.

Provides connection verification for the local Ollama LLM server.
"""

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("synapseos.ollama")


class OllamaManager:
    """Manages connectivity checks for the Ollama LLM server."""

    async def health_check(self) -> dict[str, Any]:
        """Verify Ollama is reachable by calling its health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.ollama_host}/api/tags")
                response.raise_for_status()
            return {"status": "healthy", "url": settings.ollama_host}
        except httpx.ConnectError:
            return {"status": "unavailable", "error": "Ollama server not reachable"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}


ollama_manager = OllamaManager()
