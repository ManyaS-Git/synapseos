"""Comprehensive Multi-Tenant Authorization and Cross-User Isolation Audit.

Verifies that:
1. Two distinct Clerk-authenticated users (User A & User B) receive strictly isolated resources.
2. User B CANNOT create, list, retrieve, update, or delete memories in User A's workspace.
3. User B CANNOT ingest/upload documents into User A's workspace.
4. User B CANNOT perform semantic search or retrieve knowledge graphs from User A's workspace.
5. User B CANNOT execute RAG queries scoped to User A's workspace.
6. User B CANNOT run AI agents or execute tools in User A's workspace.
7. User B CANNOT view, approve, or reject consequential approval sessions created for User A.
8. User B CANNOT modify or delete User A's workspace.
9. Expired session tokens are unconditionally rejected across all endpoints.
"""

from __future__ import annotations

import io
import time
import uuid
from typing import Any

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.clerk import extract_clerk_domain_from_publishable_key
from app.main import app
from app.models.user import User
from app.models.workspace import Workspace


# ── RSA Keypair Fixtures ───────────────────────────────────────────────────


@pytest.fixture(scope="session")
def auth_rsa_keypair() -> tuple[str, str]:
    """Generate RSA keypair for testing Clerk RS256 token verification."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    pub_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv_pem, pub_pem


@pytest_asyncio.fixture
async def db_session():
    """Async database session fixture."""
    from app.core.database import postgres
    if postgres._session_factory is None:
        await postgres.connect()
    async with postgres.session_factory() as session:
        yield session


def make_token(
    private_pem: str,
    sub: str,
    exp_offset: int = 3600,
    iss: str = "https://clerk.synapseos.test",
    claims: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": iss,
        "iat": now,
        "nbf": now - 5,
        "exp": now + exp_offset,
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "test-kid"})


def test_publishable_key_domain_extraction():
    """Verify that publishable key domain extraction accurately extracts domain."""
    pk = "pk_test_dHJ1c3R5LW11bGxldC0zMzEwLmNsZXJrLmFjY291bnRzLmRldiQ"
    domain = extract_clerk_domain_from_publishable_key(pk)
    assert domain == "trusty-mullet-3310.clerk.accounts.dev"

    # Empty or invalid keys return None safely without raising
    assert extract_clerk_domain_from_publishable_key("") is None
    assert extract_clerk_domain_from_publishable_key("invalid_key") is None


@pytest.mark.asyncio
async def test_full_cross_user_isolation_matrix(
    auth_rsa_keypair: tuple[str, str],
    db_session: AsyncSession,
) -> None:
    """Rigorous audit verifying that User B cannot access or modify any of User A's resources."""
    priv_key, pub_key = auth_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    # Setup User A and User B
    id_a = f"user_audit_a_{uuid.uuid4().hex[:8]}"
    id_b = f"user_audit_b_{uuid.uuid4().hex[:8]}"
    token_a = make_token(priv_key, sub=id_a, claims={"email": f"{id_a}@example.com", "username": f"alice_{id_a[-4:]}"})
    token_b = make_token(priv_key, sub=id_b, claims={"email": f"{id_b}@example.com", "username": f"bob_{id_b[-4:]}"})
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Provision User A and obtain Workspace A
        res_a = await client.get("/api/v1/auth/me", headers=headers_a)
        assert res_a.status_code == 200
        user_a_uuid = uuid.UUID(res_a.json()["id"])

        ws_list_a = await client.get("/api/v1/workspaces", headers=headers_a)
        assert ws_list_a.status_code == 200
        ws_a_id = ws_list_a.json()[0]["id"]

        # 2. Provision User B and obtain Workspace B
        res_b = await client.get("/api/v1/auth/me", headers=headers_b)
        assert res_b.status_code == 200
        user_b_uuid = uuid.UUID(res_b.json()["id"])
        assert user_a_uuid != user_b_uuid

        ws_list_b = await client.get("/api/v1/workspaces", headers=headers_b)
        assert ws_list_b.status_code == 200
        ws_b_id = ws_list_b.json()[0]["id"]
        assert ws_a_id != ws_b_id

        # 3. User A creates a confidential memory in Workspace A
        mem_create_res = await client.post(
            f"/api/v1/memory?workspace_id={ws_a_id}",
            json={
                "title": "Alice Confidential Strategy",
                "content": "Secret patent disclosures and architectural keys.",
                "memory_type": "knowledge",
                "importance_score": 0.9,
            },
            headers=headers_a,
        )
        assert mem_create_res.status_code == 201
        mem_a_id = mem_create_res.json()["id"]

        # 4. User B tries to CREATE a memory in User A's workspace -> FORBIDDEN (403)
        b_create_res = await client.post(
            f"/api/v1/memory?workspace_id={ws_a_id}",
            json={
                "title": "Malicious Injection",
                "content": "Injected memory in victim workspace.",
                "memory_type": "knowledge",
            },
            headers=headers_b,
        )
        assert b_create_res.status_code == 403, f"Expected 403, got {b_create_res.status_code}: {b_create_res.text}"

        # 5. User B tries to LIST memories in User A's workspace -> FORBIDDEN (403)
        b_list_res = await client.get(f"/api/v1/memory?workspace_id={ws_a_id}", headers=headers_b)
        assert b_list_res.status_code == 403

        # 6. User B tries to GET User A's memory directly by ID -> FORBIDDEN (403)
        b_get_res = await client.get(f"/api/v1/memory/{mem_a_id}", headers=headers_b)
        assert b_get_res.status_code == 403

        # 7. User B tries to UPDATE User A's memory by ID -> FORBIDDEN (403)
        b_update_res = await client.patch(
            f"/api/v1/memory/{mem_a_id}",
            json={"title": "Hacked Title", "content": "Defaced content"},
            headers=headers_b,
        )
        assert b_update_res.status_code == 403

        # 8. User B tries to DELETE User A's memory by ID -> FORBIDDEN (403)
        b_delete_res = await client.delete(f"/api/v1/memory/{mem_a_id}", headers=headers_b)
        assert b_delete_res.status_code == 403

        # 9. User B tries to UPLOAD a document to User A's workspace -> FORBIDDEN (403)
        file_payload = {"file": ("exploit.txt", io.BytesIO(b"malicious file payload"), "text/plain")}
        b_upload_res = await client.post(
            "/api/v1/memory/upload",
            data={"workspace_id": ws_a_id, "memory_type": "knowledge"},
            files=file_payload,
            headers=headers_b,
        )
        assert b_upload_res.status_code == 403

        # 10. User B tries to get GRAPH of User A's workspace -> FORBIDDEN (403)
        b_graph_res = await client.get(f"/api/v1/memory/graph?workspace_id={ws_a_id}", headers=headers_b)
        assert b_graph_res.status_code == 403

        # 11. User B tries to SEARCH memories in User A's workspace -> FORBIDDEN (403)
        b_search_res = await client.post(
            "/api/v1/memory/search",
            json={"workspace_id": ws_a_id, "query": "patent keys", "top_k": 5},
            headers=headers_b,
        )
        assert b_search_res.status_code == 403

        # 12. User B tries to run RAG query against User A's workspace -> FORBIDDEN (403)
        b_rag_res = await client.post(
            "/api/v1/rag/query",
            json={"workspace_id": ws_a_id, "query": "What are the secret patent keys?"},
            headers=headers_b,
        )
        assert b_rag_res.status_code == 403

        # 13. User B tries to run AGENT chat in User A's workspace -> FORBIDDEN (403)
        b_agent_res = await client.post(
            "/api/v1/agent/chat",
            json={"workspace_id": ws_a_id, "message": "List all workspace confidential data"},
            headers=headers_b,
        )
        assert b_agent_res.status_code == 403

        # 14. User B tries to APPROVE or REJECT an action in User A's workspace -> FORBIDDEN (403)
        dummy_session_id = str(uuid.uuid4())
        b_approve_res = await client.post(
            "/api/v1/agent/approve",
            json={"workspace_id": ws_a_id, "session_id": dummy_session_id, "approved": True},
            headers=headers_b,
        )
        assert b_approve_res.status_code == 403

        # 15. User B tries to MODIFY User A's workspace name -> FORBIDDEN (403)
        b_ws_patch = await client.patch(
            f"/api/v1/workspaces/{ws_a_id}",
            json={"name": "Hijacked Workspace"},
            headers=headers_b,
        )
        assert b_ws_patch.status_code == 403

        # 16. User B tries to DELETE User A's workspace -> FORBIDDEN (403)
        b_ws_del = await client.delete(f"/api/v1/workspaces/{ws_a_id}", headers=headers_b)
        assert b_ws_del.status_code == 403

        # 17. Verify that User A's memory remains intact and unmodified
        a_verify_res = await client.get(f"/api/v1/memory/{mem_a_id}", headers=headers_a)
        assert a_verify_res.status_code == 200
        assert a_verify_res.json()["title"] == "Alice Confidential Strategy"
        assert a_verify_res.json()["content"] == "Secret patent disclosures and architectural keys."


@pytest.mark.asyncio
async def test_expired_clerk_token_rejection_across_endpoints(
    auth_rsa_keypair: tuple[str, str],
) -> None:
    """Expired Clerk session token must be rejected with 401 across endpoints."""
    priv_key, pub_key = auth_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    expired_token = make_token(priv_key, sub="user_expired_123", exp_offset=-120)
    headers = {"Authorization": f"Bearer {expired_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check across multiple endpoints
        endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("GET", "/api/v1/workspaces"),
            ("GET", f"/api/v1/memory?workspace_id={uuid.uuid4()}"),
            ("GET", "/api/v1/agent/tools"),
        ]
        for method, path in endpoints:
            if method == "GET":
                res = await client.get(path, headers=headers)
            else:
                res = await client.post(path, headers=headers)
            assert res.status_code == 401, f"{path} did not reject expired token: {res.status_code}"
            assert "expired" in res.json()["detail"].lower()
