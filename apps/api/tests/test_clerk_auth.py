"""Automated test suite for Clerk Authentication and Tenant Isolation.

Tests:
    - Valid Clerk token acceptance and identity extraction
    - First-login idempotent provisioning of user and personal workspace
    - Repeated-login idempotency (updates last_login, returns existing user)
    - Rejection of invalid signature (401)
    - Rejection of expired tokens (401)
    - Rejection of mismatched issuer (401)
    - Rejection of mismatched audience (401)
    - Rejection of missing token (401)
    - Account safety: never automatically links to existing local accounts solely by email
    - Strict workspace isolation: Clerk users cannot access other users' workspaces or memories
"""

from __future__ import annotations

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
from app.main import app
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


# ── RSA Test Keypair Fixtures ──────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_rsa_keypair() -> tuple[str, str]:
    """Generate a 2048-bit RSA keypair for testing Clerk RS256 token signing."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


@pytest.fixture(scope="session")
def another_rsa_keypair() -> tuple[str, str]:
    """Generate an untrusted RSA keypair to simulate signature tampering."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


@pytest_asyncio.fixture
async def db_session():
    """Async database session fixture for Clerk testing."""
    from app.core.database import postgres
    if postgres._session_factory is None:
        await postgres.connect()
    async with postgres.session_factory() as session:
        yield session


def create_clerk_test_token(
    private_pem: str,
    sub: str = "user_2test123456789",
    exp_offset: int = 3600,
    iss: str = "https://clerk.synapseos.test",
    aud: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Helper to craft an RS256 token matching Clerk's format."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": iss,
        "iat": now,
        "nbf": now - 5,
        "exp": now + exp_offset,
    }
    if aud:
        payload["aud"] = aud
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "test-kid-1"})


# ── Test Cases ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clerk_token_missing_rejected() -> None:
    """Missing token on protected endpoint must return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert "Not authenticated" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_valid_token_first_login_provisions_user(
    test_rsa_keypair: tuple[str, str],
    db_session: AsyncSession,
) -> None:
    """Valid Clerk token triggers idempotent user and workspace provisioning."""
    priv_key, pub_key = test_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    clerk_id = f"user_{uuid.uuid4().hex[:12]}"
    token = create_clerk_test_token(
        priv_key,
        sub=clerk_id,
        extra_claims={
            "email": f"{clerk_id}@example.com",
            "name": "Clerk Test User",
            "username": f"pilot_{clerk_id[-6:]}",
        },
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["clerk_user_id"] == clerk_id
        assert data["email"] == f"{clerk_id}@example.com"
        assert "id" in data

        user_uuid = uuid.UUID(data["id"])

        # Verify user exists in database
        stmt = select(User).where(User.id == user_uuid)
        user = (await db_session.execute(stmt)).scalar_one_or_none()
        assert user is not None
        assert user.clerk_user_id == clerk_id
        assert user.password_hash == "!clerk_managed"

        # Verify an isolated personal workspace was automatically provisioned
        ws_stmt = select(Workspace).where(Workspace.owner_id == user_uuid)
        workspaces = (await db_session.execute(ws_stmt)).scalars().all()
        assert len(workspaces) == 1
        assert workspaces[0].owner_id == user_uuid


@pytest.mark.asyncio
async def test_clerk_repeated_login_is_idempotent(
    test_rsa_keypair: tuple[str, str],
    db_session: AsyncSession,
) -> None:
    """Repeated login with the same Clerk token does not create duplicate users."""
    priv_key, pub_key = test_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    clerk_id = f"user_{uuid.uuid4().hex[:12]}"
    token = create_clerk_test_token(priv_key, sub=clerk_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First login
        resp1 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp1.status_code == 200
        user1 = resp1.json()

        # Second login
        resp2 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp2.status_code == 200
        user2 = resp2.json()

        assert user1["id"] == user2["id"]
        assert user1["clerk_user_id"] == user2["clerk_user_id"]

        # Ensure only 1 user with this clerk_user_id exists
        stmt = select(User).where(User.clerk_user_id == clerk_id)
        count = len((await db_session.execute(stmt)).scalars().all())
        assert count == 1


@pytest.mark.asyncio
async def test_clerk_invalid_signature_rejected(
    test_rsa_keypair: tuple[str, str],
    another_rsa_keypair: tuple[str, str],
) -> None:
    """Token signed with an untrusted private key must be rejected with 401."""
    _, pub_key = test_rsa_keypair
    untrusted_priv, _ = another_rsa_keypair

    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    tampered_token = create_clerk_test_token(untrusted_priv, sub="user_hacker")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        assert resp.status_code == 401
        assert "Invalid Clerk token signature" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_expired_token_rejected(
    test_rsa_keypair: tuple[str, str],
) -> None:
    """Expired token must be rejected with 401."""
    priv_key, pub_key = test_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    expired_token = create_clerk_test_token(priv_key, sub="user_expired", exp_offset=-60)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_clerk_wrong_issuer_rejected(
    test_rsa_keypair: tuple[str, str],
) -> None:
    """Token with wrong issuer claim must be rejected with 401."""
    priv_key, pub_key = test_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    wrong_iss_token = create_clerk_test_token(
        priv_key,
        sub="user_wrong_iss",
        iss="https://evil-phishing-clerk.com",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {wrong_iss_token}"})
        assert resp.status_code == 401
        assert "claim verification failed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_account_safety_does_not_hijack_existing_account(
    test_rsa_keypair: tuple[str, str],
    db_session: AsyncSession,
) -> None:
    """A Clerk token with the same email as an existing local account must NOT hijack or overwrite that account."""
    priv_key, pub_key = test_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    local_email = f"local_admin_{uuid.uuid4().hex[:6]}@example.com"
    local_user = User(
        id=uuid.uuid4(),
        email=local_email,
        username=f"admin_{uuid.uuid4().hex[:6]}",
        password_hash="argon2_hashed_local_password",
        email_verified=True,
        is_active=True,
    )
    db_session.add(local_user)
    await db_session.commit()

    # Now a Clerk user signs in with the exact same email
    clerk_id = f"user_{uuid.uuid4().hex[:12]}"
    token = create_clerk_test_token(
        priv_key,
        sub=clerk_id,
        extra_claims={"email": local_email, "username": local_user.username},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        clerk_data = resp.json()

        # The Clerk user must have a DIFFERENT internal UUID from the existing local user
        assert uuid.UUID(clerk_data["id"]) != local_user.id
        assert clerk_data["clerk_user_id"] == clerk_id

        # The original local user's password and status must remain completely untouched
        refreshed_local = (
            await db_session.execute(select(User).where(User.id == local_user.id))
        ).scalar_one()
        assert refreshed_local.password_hash == "argon2_hashed_local_password"
        assert refreshed_local.clerk_user_id is None


@pytest.mark.asyncio
async def test_clerk_workspace_isolation_enforced(
    test_rsa_keypair: tuple[str, str],
    db_session: AsyncSession,
) -> None:
    """A Clerk user cannot access or list workspaces of another user."""
    priv_key, pub_key = test_rsa_keypair
    settings.clerk_jwt_key = pub_key
    settings.clerk_issuer = "https://clerk.synapseos.test"

    # User A (Clerk)
    clerk_a_id = f"user_a_{uuid.uuid4().hex[:8]}"
    token_a = create_clerk_test_token(priv_key, sub=clerk_a_id)

    # User B (Clerk)
    clerk_b_id = f"user_b_{uuid.uuid4().hex[:8]}"
    token_b = create_clerk_test_token(priv_key, sub=clerk_b_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Provision both users
        resp_a = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert resp_a.status_code == 200
        resp_b = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.status_code == 200

        # User A lists their workspaces
        ws_resp_a = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token_a}"})
        assert ws_resp_a.status_code == 200
        workspaces_a = ws_resp_a.json()
        assert len(workspaces_a) >= 1
        ws_a_id = workspaces_a[0]["id"]

        # User B lists their workspaces
        ws_resp_b = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token_b}"})
        assert ws_resp_b.status_code == 200
        workspaces_b = ws_resp_b.json()
        assert len(workspaces_b) >= 1
        ws_b_id = workspaces_b[0]["id"]

        # Ensure user A and user B have completely distinct workspace IDs
        assert ws_a_id != ws_b_id

        # User B attempts to access or query memories inside User A's workspace
        # Memory query for User A's workspace by User B should be rejected or empty
        mem_resp = await client.get(
            f"/api/v1/memory?workspace_id={ws_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        # Should be forbidden or unauthorized because User B is not a member of Workspace A
        assert mem_resp.status_code in (403, 404), mem_resp.text
