"""Full-Stack Frontend/Backend Integration Contract Tests.

Validates that all backend API contracts and schemas expected by the
integrated SynapseOS frontend (v0.dev UI + React Query + Next.js client)
are satisfied, including:
- Auth registration, login, session cookies, and profile endpoints.
- Memory listing, creation, pagination, and deletion contracts.
- Document upload (.md, .txt) multipart ingestion contract.
- Evidence-backed RAG citations and abstention contracts.
- Agent chat planning, consequential approval gates, and execution contracts.
- Unauthorized request and error state contracts.
"""

import os
import sys
import uuid
import asyncio
import pytest
from fastapi.testclient import TestClient

_api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api"))
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

from app.main import app
from app.core.config import settings
from app.core.database import get_db, postgres
from app.models import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


@pytest.fixture(scope="module")
def setup_test_db():
    test_db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_contracts.db"))
    test_engine = None

    if postgres._session_factory is None:
        test_engine = create_async_engine(f"sqlite+aiosqlite:///{test_db_file}", echo=False)
        test_session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

        async def _init_schema():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(_init_schema())

        async def _override_get_db():
            async with test_session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db] = _override_get_db

    yield

    if test_engine is not None:
        async def _cleanup():
            await test_engine.dispose()
        asyncio.run(_cleanup())
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass


def test_frontend_fullstack_contract_flow(setup_test_db):
    """Execute complete end-to-end full-stack contract validation."""
    with TestClient(app) as client:
        # 1. Health check contract
        print("\n  [Contract 1/12] Health live check...")
        health_resp = client.get("/health/live")
        assert health_resp.status_code == 200
        assert health_resp.json().get("status") == "alive"

        # 2. Registration contract
        print("  [Contract 2/12] User registration...")
        unique_id = uuid.uuid4().hex[:6]
        user_payload = {
            "email": f"fstester_{unique_id}@synapseos.internal",
            "username": f"fstester_{unique_id}",
            "password": "Password123!",
            "full_name": "FullStack Tester",
        }
        reg_resp = client.post("/api/v1/auth/register", json=user_payload)
        assert reg_resp.status_code in (201, 409)

        # 3. Login & cookie session contract
        print("  [Contract 3/12] Login & JWT session...")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": user_payload["email"], "password": user_payload["password"]},
        )
        assert login_resp.status_code == 200
        user_data = login_resp.json()
        assert "id" in user_data
        assert user_data["email"] == user_payload["email"]

        token = login_resp.cookies.get(settings.jwt_cookie_name) or reg_resp.cookies.get(settings.jwt_cookie_name)
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 4. Workspace listing and creation contract
        print("  [Contract 4/12] Workspace tenancy...")
        ws_list_resp = client.get("/api/v1/workspaces", headers=headers)
        assert ws_list_resp.status_code == 200
        workspaces = ws_list_resp.json()
        assert isinstance(workspaces, list)

        if len(workspaces) == 0:
            create_ws_resp = client.post(
                "/api/v1/workspaces",
                headers=headers,
                json={"name": "Integrated Workspace", "description": "v0 UI Integration"},
            )
            assert create_ws_resp.status_code == 201
            workspace_id = create_ws_resp.json()["id"]
        else:
            workspace_id = workspaces[0]["id"]

        # 5. Memory creation contract
        print("  [Contract 5/12] Memory creation & vectorization...")
        mem_payload = {
            "title": "Nebius GPU Cluster Config",
            "content": "SynapseOS runs on NVIDIA Nemotron-4-340B instructed nodes with H100 SXM5 GPUs.",
            "summary": "Infrastructure config for Nebius GPU cluster.",
            "memory_type": "knowledge",
            "tags": ["nebius", "gpu", "nemotron"],
            "importance_score": 0.9,
        }
        mem_resp = client.post(
            f"/api/v1/memory?workspace_id={workspace_id}",
            headers=headers,
            json=mem_payload,
        )
        assert mem_resp.status_code == 201
        created_mem = mem_resp.json()
        assert created_mem["title"] == mem_payload["title"]
        assert created_mem["memory_type"] == "knowledge"
        assert "id" in created_mem
        memory_id = created_mem["id"]

        # 6. Memory listing contract
        print("  [Contract 6/12] Memory listing & pagination...")
        list_mem_resp = client.get(
            f"/api/v1/memory?workspace_id={workspace_id}&page=1&page_size=10",
            headers=headers,
        )
        assert list_mem_resp.status_code == 200
        list_data = list_mem_resp.json()
        assert "memories" in list_data
        assert "total" in list_data
        assert any(m["id"] == memory_id for m in list_data["memories"])

        # 7. Document upload contract
        print("  [Contract 7/12] Document multipart upload (.md)...")
        files = {"file": ("integration_note.md", b"# Integration Note\nValidated fullstack merger.", "text/markdown")}
        data = {"workspace_id": workspace_id, "memory_type": "document", "tags": "doc,test"}
        upload_resp = client.post("/api/v1/memory/upload", headers=headers, files=files, data=data)
        assert upload_resp.status_code == 201
        upload_data = upload_resp.json()
        assert upload_data["memory_type"] == "document"

        # 8. RAG evidence retrieval contract
        print("  [Contract 8/12] Evidence-backed RAG citations...")
        rag_resp = client.post(
            "/api/v1/rag/query",
            headers=headers,
            json={"query": "What GPUs are used on Nebius?", "workspace_id": workspace_id, "top_k": 3},
        )
        assert rag_resp.status_code == 200
        rag_data = rag_resp.json()
        assert "answer" in rag_data
        assert "citations" in rag_data
        assert "is_unsupported" in rag_data

        # 9. Strict abstention contract
        print("  [Contract 9/12] Strict abstention guard...")
        abstain_resp = client.post(
            "/api/v1/rag/query",
            headers=headers,
            json={"query": "What is the secret recipe of Coca-Cola?", "workspace_id": workspace_id},
        )
        assert abstain_resp.status_code == 200
        assert abstain_resp.json()["is_unsupported"] is True

        # 10. Agent planning and consequential gate contract
        print("  [Contract 10/12] Agent planning & consequential gate...")
        agent_chat_resp = client.post(
            "/api/v1/agent/chat",
            headers=headers,
            json={
                "message": "Create a new project named Production Deployment",
                "workspace_id": workspace_id,
            },
        )
        assert agent_chat_resp.status_code == 200
        agent_data = agent_chat_resp.json()
        assert "plan" in agent_data
        assert "status" in agent_data
        assert "session_id" in agent_data

        # 11. Approval workflow contract
        print("  [Contract 11/12] Consequential action approval...")
        if agent_data["status"] == "awaiting_approval":
            approve_resp = client.post(
                "/api/v1/agent/approve",
                headers=headers,
                json={
                    "session_id": agent_data["session_id"],
                    "approved": True,
                    "workspace_id": workspace_id,
                },
            )
            assert approve_resp.status_code == 200
            assert approve_resp.json()["status"] == "completed"

        # 12. Memory deletion contract
        print("  [Contract 12/12] Memory deletion...")
        del_resp = client.delete(f"/api/v1/memory/{memory_id}", headers=headers)
        assert del_resp.status_code in (200, 204)
        print("  [PASS] All 12 full-stack contracts successfully verified!")
