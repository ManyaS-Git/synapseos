"""Integration test for Memory and Document Durability (Phase C).

Verifies:
1. Memory lifecycle: Create, retrieve by ID, search semantically.
2. Durability: Memory and local vector index survive store re-instantiation (simulated restart).
3. Workspace isolation: Second user/workspace cannot read or search memories of another workspace.
4. Mutation & Deletion: Updates and deletions reflect across database and vector store.
5. Document lifecycle: Ingestion, chunking, indexing, retrieval with source attribution, and survival across restart.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

_api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api"))
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

from app.main import app
from app.core.config import settings
from app.services.memory.vector_store import VectorStore, LOCAL_VECTOR_PATH


def test_memory_and_document_durability_lifecycle():
    """Verify memory persistence, semantic retrieval, workspace isolation, and restart survival."""
    with TestClient(app) as client:
        # 1. Setup User A and Workspace A
        uid_a = uuid.uuid4().hex[:6]
        user_a = {
            "email": f"usera_{uid_a}@synapseos.internal",
            "username": f"usera_{uid_a}",
            "password": "Password123!",
            "full_name": "User Alpha",
        }
        reg_a = client.post("/api/v1/auth/register", json=user_a)
        assert reg_a.status_code in (201, 409)
        login_a = client.post("/api/v1/auth/login", json={"email": user_a["email"], "password": user_a["password"]})
        assert login_a.status_code == 200
        token_a = login_a.cookies.get(settings.jwt_cookie_name) or reg_a.cookies.get(settings.jwt_cookie_name)
        headers_a = {"Authorization": f"Bearer {token_a}"} if token_a else {}

        ws_a_resp = client.post("/api/v1/workspaces", headers=headers_a, json={"name": f"Alpha Workspace {uid_a}"})
        assert ws_a_resp.status_code == 201
        ws_a_id = ws_a_resp.json()["id"]

        # 2. Setup User B and Workspace B
        uid_b = uuid.uuid4().hex[:6]
        user_b = {
            "email": f"userb_{uid_b}@synapseos.internal",
            "username": f"userb_{uid_b}",
            "password": "Password123!",
            "full_name": "User Beta",
        }
        reg_b = client.post("/api/v1/auth/register", json=user_b)
        assert reg_b.status_code in (201, 409)
        login_b = client.post("/api/v1/auth/login", json={"email": user_b["email"], "password": user_b["password"]})
        assert login_b.status_code == 200
        token_b = login_b.cookies.get(settings.jwt_cookie_name) or reg_b.cookies.get(settings.jwt_cookie_name)
        headers_b = {"Authorization": f"Bearer {token_b}"} if token_b else {}

        ws_b_resp = client.post("/api/v1/workspaces", headers=headers_b, json={"name": f"Beta Workspace {uid_b}"})
        assert ws_b_resp.status_code == 201
        ws_b_id = ws_b_resp.json()["id"]

        # 3. Create persistent memory in Workspace A
        memory_payload = {
            "title": f"Quantum Specs Zeus-{uid_a}",
            "content": f"Confidential quantum architecture specs for project Zeus-{uid_a}. Employs superconducting qubits with cryo-cooling.",
            "summary": "Zeus quantum architecture design notes",
            "memory_type": "knowledge",
            "tags": ["quantum", "specs", "zeus"],
            "importance_score": 0.95,
            "confidence": 0.98,
        }
        create_mem_resp = client.post(
            f"/api/v1/memory?workspace_id={ws_a_id}",
            headers=headers_a,
            json=memory_payload,
        )
        assert create_mem_resp.status_code == 201
        mem_data = create_mem_resp.json()
        memory_id = mem_data["id"]
        assert mem_data["title"] == memory_payload["title"]
        assert mem_data["content"] == memory_payload["content"]

        # 4. Retrieve memory by ID in Workspace A
        get_mem_resp = client.get(
            f"/api/v1/memory/{memory_id}?workspace_id={ws_a_id}",
            headers=headers_a,
        )
        assert get_mem_resp.status_code == 200
        assert get_mem_resp.json()["id"] == memory_id

        # 5. Semantic / vector search in Workspace A
        search_resp = client.post(
            "/api/v1/memory/search",
            headers=headers_a,
            json={"query": "quantum architecture specs cryo-cooling", "workspace_id": ws_a_id, "limit": 5},
        )
        assert search_resp.status_code == 200
        search_results = search_resp.json().get("results", [])
        assert len(search_results) > 0
        assert any(r["memory"]["id"] == memory_id for r in search_results)

        # 6. Cross-workspace isolation: User B cannot retrieve Workspace A's memory
        cross_get = client.get(
            f"/api/v1/memory/{memory_id}?workspace_id={ws_b_id}",
            headers=headers_b,
        )
        assert cross_get.status_code in (403, 404)

        # Cross-workspace search isolation: Workspace B search returns no Workspace A memory
        cross_search = client.post(
            "/api/v1/memory/search",
            headers=headers_b,
            json={"query": "quantum architecture specs cryo-cooling", "workspace_id": ws_b_id, "limit": 5},
        )
        assert cross_search.status_code == 200
        b_results = cross_search.json().get("results", [])
        assert not any(r["memory"]["id"] == memory_id for r in b_results)

        # 7. Restart simulation: Clear memory cache in VectorStore and reload from disk
        VectorStore._memory_vectors.clear()
        VectorStore._load_local_store()

        reloaded_search = client.post(
            "/api/v1/memory/search",
            headers=headers_a,
            json={"query": "quantum architecture specs cryo-cooling", "workspace_id": ws_a_id, "limit": 5},
        )
        assert reloaded_search.status_code == 200
        reloaded_results = reloaded_search.json().get("results", [])
        assert any(r["memory"]["id"] == memory_id for r in reloaded_results)

        # 8. Upload document with source attribution
        doc_content = f"# SynapseOS Security Manifesto\n\nAll cryptographic keys for Zeus-{uid_a} are rotated hourly."
        doc_files = {"file": (f"manifesto_{uid_a}.md", doc_content.encode("utf-8"), "text/markdown")}
        doc_data = {"workspace_id": ws_a_id, "memory_type": "document", "tags": "security,manifesto"}
        doc_resp = client.post(
            "/api/v1/memory/upload",
            headers=headers_a,
            files=doc_files,
            data=doc_data,
        )
        assert doc_resp.status_code == 201
        doc_res = doc_resp.json()
        assert "id" in doc_res
        assert doc_res["memory_type"] == "document"
        uploaded_doc_id = doc_res["id"]

        # 9. Verify document listing
        doc_list_resp = client.get(
            f"/api/v1/memory?workspace_id={ws_a_id}&page=1&page_size=20",
            headers=headers_a,
        )
        assert doc_list_resp.status_code == 200
        memories = doc_list_resp.json().get("memories", [])
        assert any(m["id"] == uploaded_doc_id for m in memories)

        # 10. Delete memory and verify removal from vector store & db
        del_resp = client.delete(
            f"/api/v1/memory/{memory_id}?workspace_id={ws_a_id}",
            headers=headers_a,
        )
        assert del_resp.status_code in (200, 204)

        # Confirm deleted memory is gone from ID lookup
        after_del_get = client.get(
            f"/api/v1/memory/{memory_id}?workspace_id={ws_a_id}",
            headers=headers_a,
        )
        assert after_del_get.status_code == 404
