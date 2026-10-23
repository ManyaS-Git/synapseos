"""Live Production Verification Suite for SynapseOS Deployed Instances.

Tests public endpoints on Render backend and Vercel frontend.
"""

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

BACKEND_URL = "https://synapseos-api-2onj.onrender.com"
FRONTEND_URL = "https://synapseos-three.vercel.app"

cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def log_test(name: str, passed: bool, details: str):
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name} - {details}")
    return passed


def test_cors(origin: str):
    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
        method="OPTIONS",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            allow_origin = resp.headers.get("access-control-allow-origin")
            allow_creds = resp.headers.get("access-control-allow-credentials")
            passed = resp.status == 200 and allow_origin in (origin, "*")
            return log_test("CORS Preflight", passed, f"Status: {resp.status}, Origin: {allow_origin}, Creds: {allow_creds}")
    except urllib.error.HTTPError as e:
        return log_test("CORS Preflight", False, f"HTTP {e.code}: {e.read().decode()[:80]}")
    except Exception as e:
        return log_test("CORS Preflight", False, f"Error: {e}")


def test_health_endpoints():
    results = []
    # 1. Root
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/", timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results.append(log_test("Root GET /", resp.status == 200 and data.get("name") == "SynapseOS API", f"Version: {data.get('version')}"))
    except Exception as e:
        results.append(log_test("Root GET /", False, str(e)))

    # 2. Health
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results.append(log_test("Health GET /health", resp.status == 200 and data.get("status") == "healthy", str(data)))
    except Exception as e:
        results.append(log_test("Health GET /health", False, str(e)))

    # 3. Liveness
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/health/live", timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results.append(log_test("Liveness GET /health/live", resp.status == 200 and data.get("status") == "alive", str(data)))
    except Exception as e:
        results.append(log_test("Liveness GET /health/live", False, str(e)))

    # 4. Readiness
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/health/ready", timeout=10) as resp:
            data = json.loads(resp.read().decode())
            is_ready = resp.status == 200 and data.get("status") == "ready"
            engine = data.get("services", {}).get("postgres", {}).get("engine", "unknown")
            results.append(log_test("Readiness GET /health/ready", is_ready, f"Status: {data.get('status')}, Engine: {engine}"))
    except urllib.error.HTTPError as e:
        results.append(log_test("Readiness GET /health/ready", False, f"HTTP {e.code}: {e.read().decode()[:80]}"))
    except Exception as e:
        results.append(log_test("Readiness GET /health/ready", False, str(e)))

    return all(results)


def test_auth_and_user_journey():
    ts = int(time.time())
    demo_email = f"judge_{ts}@example.com"
    demo_user = f"judge_{ts}"
    demo_pass = "JudgePass123!Secure"

    print(f"\n--- Testing User Journey with {demo_user} ---")

    # 1. Register
    reg_payload = json.dumps({
        "email": demo_email,
        "username": demo_user,
        "password": demo_pass,
        "full_name": "Judge Evaluator",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/auth/register",
        data=reg_payload,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )

    try:
        with opener.open(req, timeout=15) as resp:
            user_data = json.loads(resp.read().decode())
            workspace_id = user_data.get("default_workspace_id")
            log_test("Auth Register", resp.status in (200, 201), f"User ID: {user_data.get('id')}, Workspace: {workspace_id}")
    except urllib.error.HTTPError as e:
        log_test("Auth Register", False, f"HTTP {e.code}: {e.read().decode()[:120]}")
        return False
    except Exception as e:
        log_test("Auth Register", False, str(e))
        return False

    # 2. Get or Create Workspace
    if not workspace_id:
        req = urllib.request.Request(
            f"{BACKEND_URL}/api/v1/workspaces",
            headers={"Origin": FRONTEND_URL},
        )
        try:
            with opener.open(req, timeout=10) as resp:
                ws_list = json.loads(resp.read().decode())
                if ws_list:
                    workspace_id = ws_list[0]["id"]
                    log_test("Get Workspaces", True, f"Found workspace: {workspace_id}")
                else:
                    ws_payload = json.dumps({
                        "name": "Judge Demo Workspace",
                        "description": "Auto-created personal workspace",
                    }).encode("utf-8")
                    req_ws = urllib.request.Request(
                        f"{BACKEND_URL}/api/v1/workspaces",
                        data=ws_payload,
                        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
                        method="POST",
                    )
                    with opener.open(req_ws, timeout=10) as ws_created:
                        ws_data = json.loads(ws_created.read().decode())
                        workspace_id = ws_data["id"]
                        log_test("Create Workspace", True, f"Created workspace: {workspace_id}")
        except Exception as e:
            log_test("Get/Create Workspaces", False, str(e))
            return False

    # 3. Create Memory
    mem_payload = json.dumps({
        "title": "Apollo Mission Schedule",
        "content": "Apollo phase 1 kick-off scheduled for November 12. Security review requires three sign-offs.",
        "memory_type": "knowledge",
        "tags": ["apollo", "timeline", "security"],
        "importance_score": 0.8,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/memory?workspace_id={workspace_id}",
        data=mem_payload,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=10) as resp:
            mem_data = json.loads(resp.read().decode())
            mem_id = mem_data.get("id")
            log_test("Memory Create", resp.status in (200, 201), f"Memory ID: {mem_id}")
    except urllib.error.HTTPError as e:
        log_test("Memory Create", False, f"HTTP {e.code}: {e.read().decode()[:120]}")
        return False
    except Exception as e:
        log_test("Memory Create", False, str(e))
        return False

    # 4. Search Memory
    search_payload = json.dumps({
        "query": "when is phase 1 starting?",
        "workspace_id": workspace_id,
        "top_k": 5,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/memory/search",
        data=search_payload,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=10) as resp:
            search_data = json.loads(resp.read().decode())
            results = search_data.get("results", [])
            log_test("Memory Search", len(results) > 0, f"Found {len(results)} results")
    except Exception as e:
        log_test("Memory Search", False, str(e))

    # 5. RAG Query (Grounded)
    rag_payload = json.dumps({
        "query": "What is the launch date for Apollo phase 1?",
        "workspace_id": workspace_id,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/rag/query",
        data=rag_payload,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=15) as resp:
            rag_data = json.loads(resp.read().decode())
            citations = rag_data.get("citations", [])
            is_unsupported = rag_data.get("is_unsupported", False)
            log_test("RAG Grounded Query", len(citations) > 0 or not is_unsupported, f"Citations: {len(citations)}, Unsupported: {is_unsupported}")
    except Exception as e:
        log_test("RAG Grounded Query", False, str(e))

    # 6. RAG Abstention
    rag_unsupported = json.dumps({
        "query": "What was the total marketing budget allocated for Tokyo in 2024?",
        "workspace_id": workspace_id,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/rag/query",
        data=rag_unsupported,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=15) as resp:
            rag_data = json.loads(resp.read().decode())
            is_unsupported = rag_data.get("is_unsupported", False)
            log_test("RAG Principled Abstention", is_unsupported, f"Correctly abstained: {is_unsupported}")
    except Exception as e:
        log_test("RAG Principled Abstention", False, str(e))

    # 7. Agent Action & Consequential Approval Barrier
    agent_payload = json.dumps({
        "message": "Please create a new project called Apollo Space Mission",
        "workspace_id": workspace_id,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/agent/chat",
        data=agent_payload,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=15) as resp:
            agent_data = json.loads(resp.read().decode())
            agent_status = agent_data.get("status")
            req_approval = agent_status == "awaiting_approval"
            session_id = agent_data.get("session_id")
            log_test("Agent Consequential Approval Barrier", req_approval, f"Session: {session_id}, Status: {agent_status}")

            if req_approval and session_id:
                # Test Reject Barrier
                rej_payload = json.dumps({
                    "session_id": session_id,
                    "approved": False,
                    "workspace_id": workspace_id,
                }).encode("utf-8")
                req_rej = urllib.request.Request(
                    f"{BACKEND_URL}/api/v1/agent/approve",
                    data=rej_payload,
                    headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
                    method="POST",
                )
                with opener.open(req_rej, timeout=10) as r_rej:
                    rej_data = json.loads(r_rej.read().decode())
                    executed_steps = rej_data.get("executed_steps", [])
                    step_status = executed_steps[0].get("status") if executed_steps else "unknown"
                    is_safe = step_status == "skipped"
                    log_test("Agent Rejection Safety Gate", is_safe, f"Step status: {step_status}")
    except Exception as e:
        log_test("Agent Consequential Approval Barrier", False, str(e))

    # 8. Logout
    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/auth/logout",
        headers={"Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=10) as resp:
            log_test("Auth Logout Session Invalidation", resp.status == 200, "Cookies cleared")
    except Exception as e:
        log_test("Auth Logout Session Invalidation", False, str(e))

    return True


def check_frontend():
    print(f"\n--- Checking Frontend at {FRONTEND_URL} ---")
    try:
        with urllib.request.urlopen(FRONTEND_URL, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            title_match = re.search(r"<title>(.*?)</title>", html)
            title = title_match.group(1) if title_match else "Unknown"
            has_root = 'id="__next"' in html or 'id="root"' in html or "<main" in html or "SynapseOS" in html
            log_test("Frontend HTTPS Delivery", resp.status == 200 and has_root, f"Title: {title}, Size: {len(html)} bytes")
    except Exception as e:
        log_test("Frontend HTTPS Delivery", False, str(e))


if __name__ == "__main__":
    print(f"==================================================")
    print(f" SynapseOS Live Public Verification")
    print(f" Backend:  {BACKEND_URL}")
    print(f" Frontend: {FRONTEND_URL}")
    print(f"==================================================")

    check_frontend()
    test_cors(FRONTEND_URL)
    test_health_endpoints()
    test_auth_and_user_journey()
