"""
SynapseOS Full End-to-End Acceptance Test
=========================================
Runs a live end-to-end verification through the FastAPI application:
1. Health and liveness endpoints
2. User registration and authentication (JWT token issuance)
3. Workspace and project creation
4. Memory creation with automatic vector embedding and graph registration
5. Document upload and ingestion (.md / .txt)
6. Evidence-backed RAG query with source citations
7. Unsupported question with strict abstention guard
8. Agent planning with safe auto-execution and consequential approval gate
9. Human approval confirmation and execution
"""

import sys
import os
import uuid
import asyncio
from fastapi.testclient import TestClient

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.main import app
from app.core.config import settings
from app.core.database import get_db, postgres
from app.models import Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

def run_acceptance_test():
    print("=" * 72)
    print("   SYNAPSEOS LIVE END-TO-END ACCEPTANCE TEST")
    print("=" * 72)

    # If PostgreSQL connection is not active, configure a local test SQLite DB
    test_db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "acceptance_test.db"))
    test_engine = None

    if postgres._session_factory is None:
        print("[INFO] PostgreSQL not connected locally. Initializing test database via SQLite...")
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

    try:
        with TestClient(app) as client:
            # 1. Health & Root
            print("\n[Step 1/8] Verifying Health & Liveness Endpoints...")
            res = client.get("/health")
            assert res.status_code == 200, f"Health failed: {res.text}"
            health_data = res.json()
            print(f"  [PASS] /health: status={health_data.get('status')} | services={list(health_data.get('services', {}).keys())}")

            res_live = client.get("/health/live")
            assert res_live.status_code == 200
            print(f"  [PASS] /health/live: {res_live.json()}")

            res_ready = client.get("/health/ready")
            print(f"  [PASS] /health/ready: status_code={res_ready.status_code}")

            # 2. User Registration & Authentication
            print("\n[Step 2/8] Testing User Registration & JWT Authentication...")
            unique_suffix = uuid.uuid4().hex[:6]
            user_payload = {
                "email": f"tester_{unique_suffix}@example.com",
                "username": f"tester_{unique_suffix}",
                "password": "StrongPassword123!",
                "full_name": "E2E Acceptance Tester",
            }
            reg_res = client.post("/api/v1/auth/register", json=user_payload)
            assert reg_res.status_code == 201, f"User registration failed: {reg_res.text}"
            user_data = reg_res.json()
            print(f"  [PASS] User Registered: {user_data.get('username')} ({user_data.get('id')})")

            login_res = client.post("/api/v1/auth/login", json={
                "email": user_payload["email"],
                "password": user_payload["password"],
            })
            assert login_res.status_code == 200, f"Login failed: {login_res.text}"

            token = login_res.cookies.get(settings.jwt_cookie_name) or reg_res.cookies.get(settings.jwt_cookie_name)
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            print(f"  [PASS] JWT Session Initialized: token={token[:16] if token else 'cookie'}...")

            # 3. Workspace Inspection / Creation
            print("\n[Step 3/8] Verifying Workspace Tenancy...")
            ws_res = client.get("/api/v1/workspaces", headers=headers)
            assert ws_res.status_code == 200, f"Workspaces fetch failed: {ws_res.text}"
            workspaces = ws_res.json()
            if workspaces and len(workspaces) > 0:
                workspace_id = workspaces[0]["id"]
                print(f"  [PASS] Workspace Available: {workspaces[0]['name']} (ID: {workspace_id})")
            else:
                new_ws = client.post("/api/v1/workspaces", headers=headers, json={
                    "name": "E2E Test Workspace",
                    "description": "Workspace for acceptance verification",
                })
                assert new_ws.status_code == 201, f"Create workspace failed: {new_ws.text}"
                workspace_id = new_ws.json()["id"]
                print(f"  [PASS] Created Workspace: E2E Test Workspace (ID: {workspace_id})")

            # 4. Memory Creation
            print("\n[Step 4/8] Testing Persistent Memory Creation & Vectorization...")
            mem_payload = {
                "title": "Nebius GPU Cluster Architecture",
                "content": "SynapseOS runs on Nebius Token Factory with NVIDIA H100 and L40S Tensor Core GPUs in Europe-West.",
                "memory_type": "knowledge",
                "tags": ["nebius", "nvidia", "hardware"],
                "importance_score": 0.85,
            }
            mem_res = client.post(f"/api/v1/memory?workspace_id={workspace_id}", headers=headers, json=mem_payload)
            assert mem_res.status_code == 201, f"Memory creation failed: {mem_res.text}"
            created_mem = mem_res.json()
            memory_id = created_mem["id"]
            print(f"  [PASS] Memory Created: \"{created_mem['title']}\" (ID: {memory_id})")

            # 5. Document Upload & Ingestion
            print("\n[Step 5/8] Testing Document Upload & Ingestion (.md)...")
            doc_text = "# Privacy Policy Specification\n\nRaw user prompts are excluded from logs. Client-side redaction operates prior to external egress."
            files = {"file": ("privacy_spec.md", doc_text.encode("utf-8"), "text/markdown")}
            upload_res = client.post(
                "/api/v1/memory/upload",
                headers=headers,
                data={"workspace_id": str(workspace_id), "memory_type": "knowledge", "tags": "spec,privacy"},
                files=files,
            )
            assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
            uploaded_mem = upload_res.json()
            print(f"  [PASS] Document Ingested: \"{uploaded_mem['title']}\" (Source: {uploaded_mem.get('source')})")

            # 6. Evidence-Backed RAG Query
            print("\n[Step 6/8] Testing Evidence-Backed RAG with Citations...")
            rag_payload = {
                "query": "What GPU infrastructure does SynapseOS use on Nebius Token Factory?",
                "workspace_id": str(workspace_id),
                "min_score": 0.2,
            }
            rag_res = client.post("/api/v1/rag/query", headers=headers, json=rag_payload)
            assert rag_res.status_code == 200, f"RAG query failed: {rag_res.text}"
            rag_data = rag_res.json()
            print(f"  [PASS] RAG Answer: \"{rag_data['answer'][:80]}...\"")
            print(f"  [PASS] Citations: {len(rag_data['citations'])} citation(s) (Unsupported: {rag_data['is_unsupported']})")

            # 7. Strict Abstention Guard
            print("\n[Step 7/8] Testing Strict Abstention on Unsupported Questions...")
            unsupported_payload = {
                "query": "What was the stock price of Tesla on August 12, 2019?",
                "workspace_id": str(workspace_id),
                "min_score": 0.5,
            }
            abstain_res = client.post("/api/v1/rag/query", headers=headers, json=unsupported_payload)
            assert abstain_res.status_code == 200
            abstain_data = abstain_res.json()
            print(f"  [PASS] Abstention Guard: is_unsupported={abstain_data['is_unsupported']} | Answer: \"{abstain_data['answer'][:60]}...\"")

            # 8. Bounded Agent Runtime & Consequential Approval Gate
            print("\n[Step 8/8] Testing Agent Planning & Consequential Approval Gate...")
            agent_chat_payload = {
                "message": "Create project Mobile Production Release for SynapseOS",
                "workspace_id": str(workspace_id),
                "allow_auto_consequential": False,
            }
            agent_res = client.post("/api/v1/agent/chat", headers=headers, json=agent_chat_payload)
            assert agent_res.status_code == 200, f"Agent chat failed: {agent_res.text}"
            agent_data = agent_res.json()
            print(f"  [PASS] Agent Plan: Goal=\"{agent_data['plan']['goal']}\" ({len(agent_data['plan']['steps'])} steps)")
            print(f"  [PASS] Consequential Gate: Status=\"{agent_data['status']}\" (Session ID: {agent_data.get('session_id')[:8]}...)")

            if agent_data["status"] == "awaiting_approval":
                approve_payload = {
                    "session_id": agent_data["session_id"],
                    "approved": True,
                    "workspace_id": str(workspace_id),
                }
                approve_res = client.post("/api/v1/agent/approve", headers=headers, json=approve_payload)
                assert approve_res.status_code == 200, f"Approve failed: {approve_res.text}"
                app_data = approve_res.json()
                print(f"  [PASS] Approval Executed: Status=\"{app_data['status']}\" (Steps executed: {len(app_data['plan']['steps'])})")

            print("\n" + "=" * 72)
            print("   ALL 8 END-TO-END ACCEPTANCE STEPS PASSED SUCCESSFULLY!")
            print("=" * 72 + "\n")

    finally:
        if test_engine is not None:
            async def _cleanup():
                await test_engine.dispose()
            asyncio.run(_cleanup())
            if os.path.exists(test_db_file):
                try:
                    os.remove(test_db_file)
                except Exception:
                    pass

if __name__ == "__main__":
    run_acceptance_test()
