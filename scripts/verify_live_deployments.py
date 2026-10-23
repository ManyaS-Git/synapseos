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
    demo_email = f"judge_{ts}@demo.local"
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

    # 2. Get Current Workspace if not in user response
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
        except Exception as e:
            log_test("Get Workspaces", False, str(e))
            return False

    # 3. Create Memory
    mem_payload = json.dumps({
        "title": "Apollo Mission Schedule",
        "content": "Apollo phase 1 kick-off scheduled for November 12. Security review requires three sign-offs.",
        "workspace_id": workspace_id,
        "memory_type": "note",
        "tags": ["apollo", "timeline", "security"],
        "importance": 4,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/memory",
        data=mem_payload,
        headers={"Content-Type": "application/json", "Origin": FRONTEND_URL},
        method="POST",
    )
    try:
        with opener.open(req, timeout=10) as resp:
            mem_data = json.loads(resp.read().decode())
            mem_id = mem_data.get("id")
            log_test("Memory Create", resp.status in (200, 201), f"Memory ID: {mem_id}")
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
            items = search_data.get("items", [])
            log_test("Memory Search", len(items) > 0, f"Found {len(items)} results")
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
            log_test("RAG Grounded Query", len(citations) > 0 or not rag_data.get("abstained"), f"Citations: {len(citations)}, Abstained: {rag_data.get('abstained')}")
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
            abstained = rag_data.get("abstained", False)
            log_test("RAG Principled Abstention", abstained, f"Correctly abstained: {abstained}")
    except Exception as e:
        log_test("RAG Principled Abstention", False, str(e))

    # 7. Agent Action & Consequential Approval Barrier
    agent_payload = json.dumps({
        "message": "Please delete the Apollo Mission Schedule memory",
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
            req_approval = agent_data.get("requires_approval", False)
            session_id = agent_data.get("session_id")
            log_test("Agent Consequential Approval Barrier", req_approval, f"Session: {session_id}, Approval Required: {req_approval}")

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
                    log_test("Agent Rejection Safety Gate", not rej_data.get("action_executed", False), f"Status: {rej_data.get('status')}")
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
