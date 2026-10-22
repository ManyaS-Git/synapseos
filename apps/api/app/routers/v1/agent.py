"""Agent execution endpoints — planning, tool authorization, execution, and reflection."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runtime import (
    AgentApprovalRequest,
    AgentChatRequest,
    AgentChatResponse,
    AgentRuntime,
)
from app.agents.tools import TOOL_REGISTRY
from app.core.database import get_db
from app.core.exceptions import ForbiddenException
from app.core.security import get_current_active_user
from app.models.user import User
from app.repositories.workspace import WorkspaceRepository

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_agent(
    body: AgentChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AgentChatResponse:
    """Send an instruction to the SynapseOS agent.

    Executes planning, safe tool execution, and reflection. If any planned action
    is consequential, pauses with status 'awaiting_approval'.
    """
    workspace_repo = WorkspaceRepository(db)
    is_member = await workspace_repo.is_member(body.workspace_id, current_user.id)
    if not is_member:
        raise ForbiddenException("You are not a member of this workspace")

    runtime = AgentRuntime(db)
    return await runtime.run(body, current_user)


@router.post("/approve", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
async def approve_agent_action(
    body: AgentApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AgentChatResponse:
    """Approve or reject a pending consequential agent action."""
    workspace_repo = WorkspaceRepository(db)
    is_member = await workspace_repo.is_member(body.workspace_id, current_user.id)
    if not is_member:
        raise ForbiddenException("You are not a member of this workspace")

    runtime = AgentRuntime(db)
    return await runtime.handle_approval(body, current_user)


@router.get("/tools", status_code=status.HTTP_200_OK)
async def list_registered_tools(
    current_user: User = Depends(get_current_active_user),
) -> list[dict]:
    """List all registered and authorized tools available to the agent."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "is_consequential": tool.is_consequential,
            "parameters": tool.args_schema.model_json_schema(),
        }
        for tool in TOOL_REGISTRY.values()
    ]
