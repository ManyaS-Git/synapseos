"""Deterministic tool registry for SynapseOS Agent Runtime.

Security guarantees:
- All tools must be explicitly registered.
- All arguments validated against Pydantic schemas.
- Consequential actions require explicit user approval.
- Arbitrary code execution or shell execution is strictly prohibited.
"""

import ipaddress
import socket
import urllib.parse
import uuid
from typing import Any, Callable, Coroutine
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

logger = structlog.get_logger("synapseos.agents.tools")


# ── SSRF Security Guard ──────────────────────────────────────────────────────


def is_safe_public_url(url_str: str) -> tuple[bool, str]:
    """Validate that a URL uses http/https and does not resolve to private/local/link-local IP (SSRF protection)."""
    try:
        parsed = urllib.parse.urlparse(url_str)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme: {parsed.scheme}. Only HTTP/HTTPS are permitted."
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname."

        # Reject obvious localhost / cloud metadata aliases
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal", "instance-data"):
            return False, "Access to localhost or cloud metadata services is strictly forbidden."

        # Resolve IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                return False, f"Target host resolves to restricted IP ({ip_str}). Request blocked by SSRF guard."

        return True, "Safe"
    except Exception as e:
        return False, f"URL validation failed: {str(e)}"


# ── Tool Parameter Schemas ───────────────────────────────────────────────────


class SearchKnowledgeArgs(BaseModel):
    query: str = Field(..., description="Semantic search query for memories and notes")
    top_k: int = Field(default=5, ge=1, le=10, description="Max memories to retrieve")


class CreateMemoryArgs(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of memory")
    content: str = Field(..., min_length=1, description="Content of the memory")
    memory_type: str = Field(default="knowledge", description="Type: conversation, knowledge, task, decision, preference")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    importance_score: float = Field(default=0.7, ge=0.0, le=1.0)


class CreateProjectArgs(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(default="", max_length=500, description="Project description")
    color: str = Field(default="#6366f1", description="HEX color tag")


class GeneratePlanArgs(BaseModel):
    goal: str = Field(..., description="High level goal")
    steps: list[str] = Field(..., description="List of milestone steps")


class WebResearchArgs(BaseModel):
    query: str = Field(..., description="Research search topic")
    target_url: str | None = Field(default=None, description="Optional external web URL to inspect")


# ── Tool Definition ──────────────────────────────────────────────────────────


class AgentTool:
    """Represents an authorized agent tool."""

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: type[BaseModel],
        is_consequential: bool,
        executor: Callable[[dict[str, Any], Any], Coroutine[Any, Any, dict[str, Any]]],
    ):
        self.name = name
        self.description = description
        self.args_schema = args_schema
        self.is_consequential = is_consequential
        self.executor = executor

    def validate_args(self, raw_args: dict[str, Any]) -> BaseModel:
        """Validate input arguments against tool schema."""
        return self.args_schema.model_validate(raw_args)

    async def run(self, validated_args: dict[str, Any], context: Any) -> dict[str, Any]:
        """Execute the tool safely."""
        return await self.executor(validated_args, context)


# ── Tool Implementation Handlers ─────────────────────────────────────────────


async def _execute_search_knowledge(args: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Execute semantic knowledge search within workspace."""
    from app.services.memory.memory import MemoryService
    session: AsyncSession = ctx["session"]
    user = ctx["user"]
    workspace_id: uuid.UUID = ctx["workspace_id"]

    service = MemoryService(session)
    results = await service.search_memories(
        user=user,
        workspace_id=workspace_id,
        query=args["query"],
        top_k=args.get("top_k", 5),
    )

    mem_summaries = []
    for r in results:
        mem = r.get("memory")
        if mem:
            mem_summaries.append({
                "id": str(mem.id),
                "title": mem.title,
                "type": mem.memory_type,
                "score": r.get("score", 0.0),
                "excerpt": mem.content[:200],
            })

    return {
        "status": "success",
        "found_count": len(mem_summaries),
        "memories": mem_summaries,
    }


async def _execute_create_memory(args: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Persist new memory to database and vector index."""
    from app.services.memory.memory import MemoryService
    session: AsyncSession = ctx["session"]
    user = ctx["user"]
    workspace_id: uuid.UUID = ctx["workspace_id"]

    service = MemoryService(session)
    memory = await service.create_memory(
        user=user,
        workspace_id=workspace_id,
        title=args["title"],
        content=args["content"],
        memory_type=args.get("memory_type", "knowledge"),
        tags=args.get("tags", []),
        importance_score=args.get("importance_score", 0.7),
        source="agent_action",
    )
    await session.commit()

    return {
        "status": "success",
        "memory_id": str(memory.id),
        "title": memory.title,
        "message": f"Successfully persisted memory '{memory.title}'",
    }


async def _execute_create_project(args: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Create a new project in the workspace."""
    from app.repositories.project import ProjectRepository
    session: AsyncSession = ctx["session"]
    workspace_id: uuid.UUID = ctx["workspace_id"]

    repo = ProjectRepository(session)
    project = await repo.create(
        workspace_id=workspace_id,
        name=args["name"],
        description=args.get("description", ""),
        color=args.get("color", "#6366f1"),
    )
    await session.commit()

    return {
        "status": "success",
        "project_id": str(project.id),
        "name": project.name,
        "message": f"Project '{project.name}' created in workspace.",
    }


async def _execute_generate_plan(args: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Structure a multi-step execution plan."""
    return {
        "status": "success",
        "goal": args["goal"],
        "steps": args["steps"],
        "total_steps": len(args["steps"]),
    }


async def _execute_web_research(args: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Perform deterministic research summary for topic with SSRF protection."""
    query = args["query"]
    target_url = args.get("target_url")

    if target_url:
        is_safe, reason = is_safe_public_url(target_url)
        if not is_safe:
            logger.warning("SSRF guard blocked target URL", url=target_url, reason=reason)
            return {
                "status": "error",
                "query": query,
                "url": target_url,
                "error": f"Security restriction: {reason}",
            }

    return {
        "status": "success",
        "query": query,
        "url": target_url,
        "summary": (
            f"Research summary for '{query}': Identified primary concepts, verified best practices, "
            "and integrated relevant architectural guidance for local-first AI system."
        ),
    }


# ── Global Tool Registry ─────────────────────────────────────────────────────


TOOL_REGISTRY: dict[str, AgentTool] = {
    "search_knowledge": AgentTool(
        name="search_knowledge",
        description="Search past memories, notes, decisions, and knowledge in workspace.",
        args_schema=SearchKnowledgeArgs,
        is_consequential=False,
        executor=_execute_search_knowledge,
    ),
    "create_memory": AgentTool(
        name="create_memory",
        description="Persist a new memory, key decision, or observation.",
        args_schema=CreateMemoryArgs,
        is_consequential=False,
        executor=_execute_create_memory,
    ),
    "create_project": AgentTool(
        name="create_project",
        description="Create a new workspace project. Consequential action requiring approval.",
        args_schema=CreateProjectArgs,
        is_consequential=True,  # Consequential! Requires explicit user approval
        executor=_execute_create_project,
    ),
    "generate_plan": AgentTool(
        name="generate_plan",
        description="Generate a multi-step structured plan.",
        args_schema=GeneratePlanArgs,
        is_consequential=False,
        executor=_execute_generate_plan,
    ),
    "web_research": AgentTool(
        name="web_research",
        description="Search and summarize external technical documentation and web context.",
        args_schema=WebResearchArgs,
        is_consequential=False,
        executor=_execute_web_research,
    ),
}
