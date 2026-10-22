"""Tests for SynapseOS Agent Runtime, Tool Authorization, and Reflection."""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.runtime import (
    AgentApprovalRequest,
    AgentChatRequest,
    AgentChatResponse,
    AgentPlan,
    AgentRuntime,
    AgentStep,
    PENDING_SESSIONS,
)
from app.agents.tools import TOOL_REGISTRY, CreateMemoryArgs, CreateProjectArgs
from app.models.user import User
from app.reflection.engine import ReflectionEngine, ReflectionSummary


@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(),
        email="test@synapseos.local",
        username="testagent",
        is_active=True,
    )


def test_tool_registry_schemas():
    """Tool arguments are strictly validated against Pydantic schemas."""
    # Valid memory creation args
    mem_args = {"title": "Design Decision", "content": "Use Nemotron on Nebius", "memory_type": "decision"}
    validated = TOOL_REGISTRY["create_memory"].validate_args(mem_args)
    assert validated.title == "Design Decision"

    # Consequential flag check
    assert TOOL_REGISTRY["create_project"].is_consequential is True
    assert TOOL_REGISTRY["search_knowledge"].is_consequential is False
    assert TOOL_REGISTRY["create_memory"].is_consequential is False


@pytest.mark.asyncio
async def test_agent_pauses_for_consequential_actions(mock_user):
    """Agent runtime pauses execution and requests approval for consequential tools."""
    mock_session = AsyncMock()
    runtime = AgentRuntime(mock_session)
    ws_id = uuid.uuid4()

    req = AgentChatRequest(
        message="Create project Mobile Client for SynapseOS",
        workspace_id=ws_id,
        allow_auto_consequential=False,
    )

    resp = await runtime.run(req, mock_user)
    assert isinstance(resp, AgentChatResponse)
    assert resp.status == "awaiting_approval"
    assert resp.pending_step is not None
    assert resp.pending_step.requires_approval is True
    assert resp.session_id in PENDING_SESSIONS


@pytest.mark.asyncio
async def test_agent_approval_execution(mock_user):
    """When user approves, the pending action executes and outcome is reflected."""
    mock_session = AsyncMock()
    runtime = AgentRuntime(mock_session)
    ws_id = uuid.uuid4()

    # Initiate consequential request
    req = AgentChatRequest(
        message="Create project Web Dashboard",
        workspace_id=ws_id,
        allow_auto_consequential=False,
    )
    init_resp = await runtime.run(req, mock_user)
    assert init_resp.status == "awaiting_approval"
    session_id = init_resp.session_id

    # Mock project repository create
    with patch("app.repositories.project.ProjectRepository.create", new_callable=AsyncMock) as mock_create_proj, \
         patch("app.reflection.engine.ReflectionEngine.reflect_and_learn", new_callable=AsyncMock) as mock_reflect:

        mock_project = AsyncMock()
        mock_project.id = uuid.uuid4()
        mock_project.name = "Web Dashboard"
        mock_create_proj.return_value = mock_project

        mock_reflect.return_value = ReflectionSummary(
            task_summary="Created project Web Dashboard",
            lessons_learned=["Project initialized with workspace boundaries."],
            confidence=0.9,
        )

        app_req = AgentApprovalRequest(
            session_id=session_id,
            approved=True,
            workspace_id=ws_id,
        )
        app_resp = await runtime.handle_approval(app_req, mock_user)

        assert app_resp.status == "completed"
        assert len(app_resp.executed_steps) > 0
        assert session_id not in PENDING_SESSIONS


@pytest.mark.asyncio
async def test_agent_rejection_cancels_action(mock_user):
    """When user declines, the action is marked skipped without executing tool."""
    mock_session = AsyncMock()
    runtime = AgentRuntime(mock_session)
    ws_id = uuid.uuid4()

    req = AgentChatRequest(
        message="Create project Experimental",
        workspace_id=ws_id,
    )
    init_resp = await runtime.run(req, mock_user)
    session_id = init_resp.session_id

    app_req = AgentApprovalRequest(
        session_id=session_id,
        approved=False,
        workspace_id=ws_id,
    )
    app_resp = await runtime.handle_approval(app_req, mock_user)

    assert app_resp.status == "completed"
    assert app_resp.executed_steps[0].status == "skipped"
    assert session_id not in PENDING_SESSIONS


@pytest.mark.asyncio
async def test_agent_safe_execution_and_reflection(mock_user):
    """Safe actions (notes, memories, research) execute directly and reflect."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = True
    mock_session.execute.return_value = mock_result
    runtime = AgentRuntime(mock_session)
    ws_id = uuid.uuid4()

    with patch("app.services.memory.memory.MemoryService.create_memory", new_callable=AsyncMock) as mock_create_mem, \
         patch("app.reflection.engine.ReflectionEngine.reflect_and_learn", new_callable=AsyncMock) as mock_reflect:

        mock_mem = MagicMock()
        mock_mem.id = uuid.uuid4()
        mock_mem.title = "Important Fact"
        mock_create_mem.return_value = mock_mem

        mock_reflect.return_value = ReflectionSummary(
            task_summary="Recorded key architectural decision",
            lessons_learned=["Stored memory for future retrieval."],
            confidence=0.9,
        )

        req = AgentChatRequest(
            message="Remember that Nebius Token Factory runs NVIDIA Nemotron-70B for our project",
            workspace_id=ws_id,
        )
        resp = await runtime.run(req, mock_user)

        assert resp.status == "completed"
        assert len(resp.executed_steps) > 0
        assert resp.reflection is not None


@pytest.mark.asyncio
async def test_web_research_tool_ssrf_protection():
    """Web research tool rejects private IPs, loopback, and cloud metadata endpoints."""
    from app.agents.tools import TOOL_REGISTRY, is_safe_public_url

    # Check SSRF validation helper directly (returns (is_safe, error_msg))
    assert is_safe_public_url("http://127.0.0.1:8000/admin")[0] is False
    assert is_safe_public_url("http://localhost:3000")[0] is False
    assert is_safe_public_url("http://169.254.169.254/latest/meta-data/")[0] is False
    assert is_safe_public_url("http://10.0.0.1/internal")[0] is False
    assert is_safe_public_url("http://192.168.1.1/secret")[0] is False
    assert is_safe_public_url("ftp://example.com/file")[0] is False

    # Execute tool with malicious internal URL and verify security error
    tool = TOOL_REGISTRY["web_research"]
    result = await tool.run(
        {"query": "AWS credentials", "target_url": "http://169.254.169.254/latest/meta-data"},
        context={},
    )
    assert result["status"] == "error"
    assert "Security restriction" in result["error"] or "forbidden" in result["error"].lower()


@pytest.mark.asyncio
async def test_cross_user_approval_forbidden(mock_user):
    """User B cannot approve or execute an action initiated by User A."""
    from app.core.exceptions import ForbiddenException

    mock_session = AsyncMock()
    runtime = AgentRuntime(mock_session)
    ws_id = uuid.uuid4()

    # User A initiates a consequential action
    req = AgentChatRequest(
        message="Create project Autonomous Agent Hub",
        workspace_id=ws_id,
        allow_auto_consequential=False,
    )
    init_resp = await runtime.run(req, mock_user)
    assert init_resp.status == "awaiting_approval"
    session_id = init_resp.session_id

    # User B attempts to approve User A's session
    user_b = User(
        id=uuid.uuid4(),
        email="attacker@synapseos.local",
        username="attacker",
        is_active=True,
    )

    app_req = AgentApprovalRequest(
        session_id=session_id,
        approved=True,
        workspace_id=ws_id,
    )

    with pytest.raises(ForbiddenException) as exc_info:
        await runtime.handle_approval(app_req, user_b)

    assert "not authorized" in exc_info.value.detail.lower() or "forbidden" in exc_info.value.detail.lower()
    # Verify the session is STILL pending and was not executed or consumed
    assert session_id in PENDING_SESSIONS
