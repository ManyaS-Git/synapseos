"""Clerk JWT verification and identity provisioning.

Independently verifies Clerk session tokens using RS256 public keys or JWKS.
Enforces token signature, expiration, issuer, and required claims.
Provisions and maps verified external Clerk identities to internal SynapseOS users and workspaces.
Never trusts client-supplied user IDs, emails, or unsigned claims.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

logger = get_logger("synapseos.security.clerk")

# In-memory cache for Clerk JWKS keys
_JWKS_CACHE: dict[str, Any] = {}
_JWKS_CACHED_AT: float = 0.0
_JWKS_CACHE_TTL_SECONDS: float = 3600.0  # 1 hour cache


def normalize_pem_public_key(key: str) -> str:
    """Normalize a PEM public key string."""
    key = key.strip()
    if not key:
        return ""
    if "BEGIN PUBLIC KEY" in key:
        return key
    # Raw base64 string without PEM headers
    lines = [key[i : i + 64] for i in range(0, len(key), 64)]
    return "-----BEGIN PUBLIC KEY-----\n" + "\n".join(lines) + "\n-----END PUBLIC KEY-----\n"


async def fetch_clerk_jwks(force_refresh: bool = False) -> dict[str, Any]:
    """Fetch and cache Clerk's JWKS public keys.
    
    Tries configured CLERK_JWKS_URL, or CLERK_ISSUER/.well-known/jwks.json,
    or the default Clerk API JWKS endpoint.
    """
    global _JWKS_CACHE, _JWKS_CACHED_AT

    now = time.time()
    if not force_refresh and _JWKS_CACHE and (now - _JWKS_CACHED_AT < _JWKS_CACHE_TTL_SECONDS):
        return _JWKS_CACHE

    jwks_url = settings.clerk_jwks_url
    if not jwks_url:
        if settings.clerk_issuer:
            issuer = settings.clerk_issuer.rstrip("/")
            jwks_url = f"{issuer}/.well-known/jwks.json"
        else:
            jwks_url = "https://api.clerk.com/v1/jwks"

    headers: dict[str, str] = {}
    if settings.clerk_secret_key and "api.clerk.com" in jwks_url:
        headers["Authorization"] = f"Bearer {settings.clerk_secret_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(jwks_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                _JWKS_CACHE = data
                _JWKS_CACHED_AT = now
                logger.info("Successfully fetched and cached Clerk JWKS", url=jwks_url)
                return data
            logger.warning(
                "Failed to fetch Clerk JWKS",
                status_code=resp.status_code,
                url=jwks_url,
            )
    except Exception as exc:
        logger.warning("Error fetching Clerk JWKS", error=str(exc), url=jwks_url)

    return _JWKS_CACHE


def is_clerk_token(token: str) -> bool:
    """Quickly check whether a JWT appears to be issued by Clerk or is RS256.
    
    Inspects token header and unverified claims without accepting them as valid.
    """
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") == "RS256":
            return True
        claims = jwt.get_unverified_claims(token)
        iss = str(claims.get("iss", ""))
        sub = str(claims.get("sub", ""))
        if "clerk" in iss or sub.startswith("user_"):
            return True
    except Exception:
        pass
    return False


async def verify_clerk_token(token: str) -> dict[str, Any]:
    """Cryptographically verify a Clerk session token.
    
    Validates RS256 signature, expiry, nbf, and issuer.
    Returns verified payload claims or raises HTTPException 401.
    """
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token header",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    alg = header.get("alg")
    if alg != "RS256":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported token algorithm: {alg}. Expected RS256.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    kid = header.get("kid")
    payload: dict[str, Any] | None = None
    expected_issuer = settings.clerk_issuer or None
    expected_audience = settings.clerk_audience or None

    # Method 1: Networkless PEM verification if CLERK_JWT_KEY is provided
    if settings.clerk_jwt_key:
        pem_key = normalize_pem_public_key(settings.clerk_jwt_key)
        try:
            payload = jwt.decode(
                token,
                pem_key,
                algorithms=["RS256"],
                issuer=expected_issuer,
                audience=expected_audience,
                options={"verify_exp": True, "verify_nbf": True, "verify_iat": True},
            )
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clerk session token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except JWTClaimsError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Clerk token claim verification failed: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Clerk token signature: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    # Method 2: JWKS key verification if CLERK_JWT_KEY was not configured
    if payload is None:
        jwks = await fetch_clerk_jwks(force_refresh=False)
        keys = jwks.get("keys", [])

        # If kid not in keys, try refreshing once
        matching_key = next((k for k in keys if k.get("kid") == kid), None) if kid else (keys[0] if keys else None)
        if not matching_key and keys:
            jwks = await fetch_clerk_jwks(force_refresh=True)
            keys = jwks.get("keys", [])
            matching_key = next((k for k in keys if k.get("kid") == kid), None) if kid else (keys[0] if keys else None)

        if not matching_key:
            logger.error("No matching JWKS key found for Clerk token verification", kid=kid)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify Clerk token: public key not available",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(
                token,
                matching_key,
                algorithms=["RS256"],
                issuer=expected_issuer,
                audience=expected_audience,
                options={"verify_exp": True, "verify_nbf": True, "verify_iat": True},
            )
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clerk session token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except JWTClaimsError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Clerk token claim verification failed: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Clerk token signature: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    clerk_user_id = payload.get("sub")
    if not clerk_user_id or not isinstance(clerk_user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identity (sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_or_create_clerk_user(
    db: AsyncSession,
    clerk_user_id: str,
    claims: dict[str, Any],
) -> User:
    """Map a verified Clerk user ID to an internal SynapseOS user.
    
    Idempotently provisions new users and isolated personal workspaces.
    Never merges with existing accounts solely by email.
    """
    # 1. Search by Clerk stable user ID
    stmt = select(User).where(User.clerk_user_id == clerk_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if user is not None:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        user.last_login = now
        user.updated_at = now
        await db.flush()
        return user

    # 2. First-login provisioning for new Clerk user
    logger.info("Provisioning new internal SynapseOS user for Clerk identity", clerk_user_id=clerk_user_id)

    # Candidate email & username from claims
    claim_email = claims.get("email")
    if not claim_email or not isinstance(claim_email, str):
        # Fallback synthetic unique email
        claim_email = f"{clerk_user_id}@clerk.synapseos.local"

    claim_name = claims.get("name") or claims.get("full_name")
    claim_username = claims.get("username")
    if not claim_username or not isinstance(claim_username, str):
        short_id = clerk_user_id.replace("user_", "")[:8]
        claim_username = f"clerk_{short_id}"

    # Guard against collisions with existing local user accounts
    # NEVER automatically link or merge accounts
    existing_by_email = (
        await db.execute(select(User).where(User.email == claim_email))
    ).scalar_one_or_none()
    if existing_by_email is not None:
        short_id = clerk_user_id.replace("user_", "")[:6]
        parts = claim_email.split("@")
        claim_email = f"{parts[0]}+clerk_{short_id}@{parts[1] if len(parts) > 1 else 'synapseos.local'}"

    existing_by_username = (
        await db.execute(select(User).where(User.username == claim_username))
    ).scalar_one_or_none()
    if existing_by_username is not None:
        short_id = clerk_user_id.replace("user_", "")[:6]
        claim_username = f"{claim_username}_{short_id}"

    new_user_id = uuid.uuid4()
    new_user = User(
        id=new_user_id,
        clerk_user_id=clerk_user_id,
        email=claim_email,
        username=claim_username,
        full_name=claim_name or claim_username,
        avatar_url=claims.get("picture") or claims.get("avatar_url") or None,
        password_hash="!clerk_managed",
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now,
        last_login=now,
    )
    db.add(new_user)
    await db.flush()

    # Provision isolated personal workspace
    workspace_id = uuid.uuid4()
    workspace = Workspace(
        id=workspace_id,
        owner_id=new_user.id,
        name=f"{claim_username}'s Workspace",
        slug=f"workspace-{str(new_user.id)[:8]}",
        description="Default personal workspace",
        created_at=now,
        updated_at=now,
    )
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=new_user.id,
        role=WorkspaceRole.OWNER,
        created_at=now,
    )
    db.add(membership)
    await db.flush()

    logger.info(
        "Successfully provisioned Clerk user and default workspace",
        user_id=str(new_user.id),
        clerk_user_id=clerk_user_id,
        workspace_id=str(workspace.id),
    )
    return new_user
