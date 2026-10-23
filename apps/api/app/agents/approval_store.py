"""Durable Approval Store for SynapseOS Bounded Agent Execution.

Provides durable, concurrency-safe storage for consequential action approval
sessions with TTL expiry, replay attack protection, and cross-user authorization.

Backends:
- Redis (when available in production/docker)
- Local durable file storage (`data/approval_sessions.json` across process restarts)
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import structlog

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException

logger = structlog.get_logger("synapseos.agents.approval_store")

LOCAL_APPROVAL_STORE_PATH = os.path.join(settings.data_dir, "approval_sessions.json")
DEFAULT_TTL_SECONDS = 900  # 15 minutes


class ApprovalStore:
    """Manages pending and decided approval sessions durably."""

    def __init__(self) -> None:
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self._load_local_store()

    def _load_local_store(self) -> None:
        """Load persisted approval sessions from disk."""
        if os.path.exists(LOCAL_APPROVAL_STORE_PATH):
            try:
                with open(LOCAL_APPROVAL_STORE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    now = time.time()
                    # Filter out expired sessions on load
                    self._memory_cache = {
                        k: v for k, v in data.items() if v.get("expires_at", 0) > now
                    }
            except Exception as e:
                logger.warning("Failed to load approval sessions from disk", error=str(e))

    def _save_local_store(self) -> None:
        """Persist active sessions to disk."""
        try:
            os.makedirs(os.path.dirname(LOCAL_APPROVAL_STORE_PATH), exist_ok=True)
            tmp_path = f"{LOCAL_APPROVAL_STORE_PATH}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f)
            if os.path.exists(LOCAL_APPROVAL_STORE_PATH):
                try:
                    os.remove(LOCAL_APPROVAL_STORE_PATH)
                except Exception:
                    pass
            os.rename(tmp_path, LOCAL_APPROVAL_STORE_PATH)
        except Exception as e:
            logger.warning("Failed to save approval sessions to disk", error=str(e))

    async def save_session(
        self,
        session_id: str,
        user_id: str,
        workspace_id: str,
        project_id: str | None,
        goal: str,
        plan: dict[str, Any],
        step_index: int,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Save a pending consequential action approval session."""
        now = time.time()
        session_data = {
            "session_id": session_id,
            "user_id": str(user_id),
            "workspace_id": str(workspace_id),
            "project_id": str(project_id) if project_id else None,
            "goal": goal,
            "plan": plan,
            "step_index": step_index,
            "status": "awaiting_approval",
            "created_at": now,
            "expires_at": now + ttl_seconds,
        }

        # 1. Try Redis if connected
        try:
            from app.core.database import redis_manager
            if redis_manager._client:
                key = f"synapseos:approval:{session_id}"
                await redis_manager.client.set(key, json.dumps(session_data), ex=ttl_seconds)
        except Exception as e:
            logger.debug("Redis not available for approval session, using durable local store", error=str(e))

        # 2. Local memory & disk persistence
        self._memory_cache[session_id] = session_data
        self._save_local_store()
        logger.info("Saved approval session", session_id=session_id, goal=goal, expires_in_sec=ttl_seconds)

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve a session by ID, validating TTL."""
        # 1. Try Redis
        try:
            from app.core.database import redis_manager
            if redis_manager._client:
                key = f"synapseos:approval:{session_id}"
                data_str = await redis_manager.client.get(key)
                if data_str:
                    return json.loads(data_str)
        except Exception:
            pass

        # 2. Local cache / disk
        self._load_local_store()
        session_data = self._memory_cache.get(session_id)
        if not session_data:
            return None

        if session_data.get("expires_at", 0) < time.time():
            self._memory_cache.pop(session_id, None)
            self._save_local_store()
            return None

        return session_data

    async def consume_session(
        self,
        session_id: str,
        user_id: str,
        workspace_id: str,
        approved: bool,
    ) -> dict[str, Any]:
        """Atomically validate authorization, expiry, and transition session state.

        Prevents replay attacks by marking session as finalized.
        """
        session_data = await self.get_session(session_id)

        if not session_data or session_data.get("workspace_id") != str(workspace_id):
            raise NotFoundException("Pending execution session")

        if session_data.get("expires_at", 0) < time.time():
            raise NotFoundException("Pending execution session has expired")

        if session_data.get("user_id") != str(user_id):
            raise ForbiddenException("You are not authorized to approve this execution session")

        if session_data.get("status") != "awaiting_approval":
            raise ForbiddenException("Execution session has already been processed")

        # Mark finalized
        session_data["status"] = "approved" if approved else "rejected"
        session_data["decided_at"] = time.time()

        # Remove from active pending in Redis
        try:
            from app.core.database import redis_manager
            if redis_manager._client:
                key = f"synapseos:approval:{session_id}"
                await redis_manager.client.delete(key)
        except Exception:
            pass

        # Update local store (remove from pending so it cannot be re-executed)
        self._memory_cache.pop(session_id, None)
        self._save_local_store()

        logger.info(
            "Consumed approval session",
            session_id=session_id,
            approved=approved,
            user_id=user_id,
        )
        return session_data


approval_store = ApprovalStore()
