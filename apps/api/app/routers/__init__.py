"""API route handlers.

Health router is always registered. Feature routers will be added as
they are implemented:
- auth: Authentication endpoints
- memory: Memory CRUD and search
- agents: Agent communication
- graph: Knowledge graph operations
- rag: RAG pipeline
- settings: User settings
"""

from app.routers.health import router as health_router

__all__ = ["health_router"]
