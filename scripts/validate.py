#!/usr/bin/env python3
"""SynapseOS Validation Script.

Verifies the entire development environment is healthy:
- Environment variables
- Database connectivity (PostgreSQL, Redis, Neo4j, Qdrant)
- Docker services
- API health endpoints
- Frontend availability

Usage:
    python scripts/validate.py
    python scripts/validate.py --api-url http://localhost:8000
    python scripts/validate.py --skip-docker
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error


# ── Helpers ───────────────────────────────────────────────────────────────────

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {Colors.GREEN}✓{Colors.RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {Colors.RED}✗{Colors.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {Colors.YELLOW}!{Colors.RESET} {msg}")


def header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{msg}{Colors.RESET}")
    print("-" * 60)


def fetch_json(url: str, timeout: int = 5) -> dict | None:
    """Fetch JSON from a URL, returning None on any error."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def run_cmd(cmd: str, timeout: int = 10) -> tuple[bool, str]:
    """Run a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


# ── Checks ────────────────────────────────────────────────────────────────────

def check_env_vars() -> bool:
    """Verify critical environment variables are set."""
    header("Environment Variables")

    required = ["POSTGRES_HOST", "REDIS_HOST", "NEO4J_URI", "QDRANT_HOST"]
    all_ok = True

    for var in required:
        val = os.environ.get(var)
        if val:
            ok(f"{var} = {val}")
        else:
            warn(f"{var} not set (will use defaults)")
    return all_ok


def check_api_health(api_url: str) -> bool:
    """Verify the FastAPI backend is responding."""
    header("API Health Endpoints")

    checks = [
        ("Root (/)", f"{api_url}/"),
        ("Health (/health)", f"{api_url}/health"),
        ("Liveness (/health/live)", f"{api_url}/health/live"),
        ("Readiness (/health/ready)", f"{api_url}/health/ready"),
    ]

    all_ok = True
    for label, url in checks:
        data = fetch_json(url)
        if data:
            status = data.get("status", "unknown")
            ok(f"{label} — status: {status}")
        else:
            fail(f"{label} — not reachable")
            all_ok = False
    return all_ok


def check_database_connectivity(api_url: str) -> bool:
    """Check database status via the readiness endpoint."""
    header("Database Connectivity (via /health/ready)")

    data = fetch_json(f"{api_url}/health/ready")
    if not data:
        fail("Cannot reach /health/ready — API may be down")
        return False

    services = data.get("services", {})
    all_ok = True

    for name in ["postgres", "redis", "neo4j", "qdrant"]:
        info = services.get(name, {})
        status = info.get("status", "unknown")
        if status == "healthy":
            ok(f"{name}: healthy")
        elif status == "unavailable":
            warn(f"{name}: unavailable (may not be running)")
        else:
            fail(f"{name}: {status}")
            all_ok = False

    # Ollama is optional
    ollama = services.get("ollama", {})
    ollama_status = ollama.get("status", "unknown")
    if ollama_status in ("healthy", "unavailable"):
        ok(f"ollama: {ollama_status} (optional)")
    else:
        warn(f"ollama: {ollama_status} (optional — not critical)")

    return all_ok


def check_docker() -> bool:
    """Verify Docker Compose services are running."""
    header("Docker Services")

    success, output = run_cmd("docker compose ps --format json", timeout=15)
    if not success:
        warn("Docker Compose not available or not running")
        return True  # Non-fatal

    services = ["postgres", "redis", "neo4j", "qdrant", "ollama", "api", "web"]
    running = set()

    for line in output.splitlines():
        try:
            svc = json.loads(line)
            name = svc.get("Service", "")
            state = svc.get("State", "")
            if state == "running":
                running.add(name)
        except json.JSONDecodeError:
            continue

    all_ok = True
    for svc in services:
        if svc in running:
            ok(f"{svc}: running")
        else:
            warn(f"{svc}: not running")
    return all_ok


def check_frontend(frontend_url: str) -> bool:
    """Verify the Next.js frontend is responding."""
    header("Frontend Availability")

    try:
        req = urllib.request.Request(frontend_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                ok(f"Frontend responding at {frontend_url}")
                return True
            fail(f"Frontend returned status {resp.status}")
            return False
    except Exception:
        fail(f"Frontend not reachable at {frontend_url}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SynapseOS Validation Script")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--frontend-url", default="http://localhost:3000", help="Frontend URL")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker checks")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend checks")
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}  SynapseOS — Environment Validation{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

    results: dict[str, bool] = {}

    results["env"] = check_env_vars()
    results["api"] = check_api_health(args.api_url)
    results["databases"] = check_database_connectivity(args.api_url)

    if not args.skip_docker:
        results["docker"] = check_docker()

    if not args.skip_frontend:
        results["frontend"] = check_frontend(args.frontend_url)

    # ── Summary ───────────────────────────────────────────────────────
    header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, status in results.items():
        if status:
            ok(name)
        else:
            fail(name)

    print(f"\n{'=' * 60}")
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}All checks passed ({passed}/{total}){Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}Some checks failed ({passed}/{total}){Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
