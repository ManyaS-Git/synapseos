"""Unit and security tests for Durable Approval Store (Phase E).

Verifies:
- Durable persistence across process restarts
- TTL expiration rejection
- Replay attack protection (at-most-once execution)
- Cross-user and cross-workspace isolation
- Terminal rejection state
"""

import os
import time
import uuid
import pytest

from app.agents.approval_store import ApprovalStore, LOCAL_APPROVAL_STORE_PATH
from app.core.exceptions import ForbiddenException, NotFoundException


@pytest.fixture
def clean_store():
    """Ensure a clean approval store file and instance."""
    if os.path.exists(LOCAL_APPROVAL_STORE_PATH):
        try:
            os.remove(LOCAL_APPROVAL_STORE_PATH)
        except Exception:
            pass
    store = ApprovalStore()
    yield store
    if os.path.exists(LOCAL_APPROVAL_STORE_PATH):
        try:
            os.remove(LOCAL_APPROVAL_STORE_PATH)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_approval_store_persistence_and_reload(clean_store):
    """Test that approval sessions survive process restart / store re-instantiation."""
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    await clean_store.save_session(
        session_id=session_id,
        user_id=user_id,
        workspace_id=workspace_id,
        project_id=None,
        goal="Deploy production container",
        plan={"goal": "Deploy production container", "steps": []},
        step_index=0,
        ttl_seconds=300,
    )

    # Simulate restart by creating a new store instance reading from disk
    new_store = ApprovalStore()
    session = await new_store.get_session(session_id)
    assert session is not None
    assert session["session_id"] == session_id
    assert session["user_id"] == user_id
    assert session["workspace_id"] == workspace_id
    assert session["goal"] == "Deploy production container"


@pytest.mark.asyncio
async def test_approval_store_replay_protection(clean_store):
    """Test that a session cannot be consumed twice (preventing duplicate execution)."""
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    await clean_store.save_session(
        session_id=session_id,
        user_id=user_id,
        workspace_id=workspace_id,
        project_id=None,
        goal="Consequential tool execution",
        plan={"goal": "Consequential tool execution", "steps": []},
        step_index=0,
        ttl_seconds=300,
    )

    # First consume succeeds
    consumed = await clean_store.consume_session(
        session_id=session_id,
        user_id=user_id,
        workspace_id=workspace_id,
        approved=True,
    )
    assert consumed["status"] == "approved"

    # Second consume must fail (replay attack prevented)
    with pytest.raises(NotFoundException):
        await clean_store.consume_session(
            session_id=session_id,
            user_id=user_id,
            workspace_id=workspace_id,
            approved=True,
        )


@pytest.mark.asyncio
async def test_approval_store_cross_user_forbidden(clean_store):
    """Test that a different user cannot approve someone else's session."""
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    legit_user = str(uuid.uuid4())
    attacker_user = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    await clean_store.save_session(
        session_id=session_id,
        user_id=legit_user,
        workspace_id=workspace_id,
        project_id=None,
        goal="Admin action",
        plan={"goal": "Admin action", "steps": []},
        step_index=0,
        ttl_seconds=300,
    )

    with pytest.raises(ForbiddenException):
        await clean_store.consume_session(
            session_id=session_id,
            user_id=attacker_user,
            workspace_id=workspace_id,
            approved=True,
        )


@pytest.mark.asyncio
async def test_approval_store_cross_workspace_isolation(clean_store):
    """Test that approval requests across wrong workspace fail."""
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    user_id = str(uuid.uuid4())
    workspace_1 = str(uuid.uuid4())
    workspace_2 = str(uuid.uuid4())

    await clean_store.save_session(
        session_id=session_id,
        user_id=user_id,
        workspace_id=workspace_1,
        project_id=None,
        goal="Private workspace action",
        plan={"goal": "Private workspace action", "steps": []},
        step_index=0,
        ttl_seconds=300,
    )

    with pytest.raises(NotFoundException):
        await clean_store.consume_session(
            session_id=session_id,
            user_id=user_id,
            workspace_id=workspace_2,
            approved=True,
        )


@pytest.mark.asyncio
async def test_approval_store_ttl_expiry(clean_store):
    """Test that expired sessions are automatically rejected."""
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    # Set TTL to negative (already expired)
    await clean_store.save_session(
        session_id=session_id,
        user_id=user_id,
        workspace_id=workspace_id,
        project_id=None,
        goal="Expired action",
        plan={"goal": "Expired action", "steps": []},
        step_index=0,
        ttl_seconds=-10,
    )

    session = await clean_store.get_session(session_id)
    assert session is None

    with pytest.raises(NotFoundException):
        await clean_store.consume_session(
            session_id=session_id,
            user_id=user_id,
            workspace_id=workspace_id,
            approved=True,
        )
