"""
Repeatable Nebius Token Factory Live Inference Verification CLI
===============================================================
Verifies real-time connectivity and inference with NVIDIA Nemotron models
hosted on Nebius Token Factory without exposing sensitive keys or prompts.

Usage:
    python scripts/verify_nebius_inference.py
    python scripts/verify_nebius_inference.py --allow-simulated
    python scripts/verify_nebius_inference.py --remote-url https://synapseos-api-2onj.onrender.com --allow-simulated
"""

import sys
import os
import argparse
import asyncio
import time
import httpx

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.core.config import settings
from app.core.llm.nebius import NebiusNemotronClient

def mask_key(key: str | None) -> str:
    """Mask API key for safe display."""
    if not key:
        return "<NOT SET>"
    if key.startswith("change-me") or key.startswith("your-"):
        return f"<PLACEHOLDER: {key}>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

async def verify_remote_backend(remote_url: str, allow_simulated: bool = False) -> int:
    """Verify live vs simulated inference against deployed SynapseOS backend."""
    clean_url = remote_url.rstrip("/")
    print("=" * 72)
    print("   SYNAPSEOS REMOTE BACKEND NEBIUS INFERENCE VERIFICATION")
    print(f"   Target URL: {clean_url}")
    print("=" * 72)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Probe readiness endpoint
        print("\n[1/3] Probing Remote Readiness Probe (/health/ready)...")
        try:
            res = await client.get(f"{clean_url}/health/ready")
            res.raise_for_status()
            ready_data = res.json()
        except Exception as e:
            print(f"[STATUS: FAILED] Failed to reach remote backend /health/ready: {e}")
            return 1

        nebius_status = ready_data.get("services", {}).get("nebius_token_factory", {})
        configured = nebius_status.get("configured", False)
        status = nebius_status.get("status", "unknown")
        model = nebius_status.get("model", "unknown")

        print(f"  Remote Engine Status: {status}")
        print(f"  Configured in Cloud:  {configured}")
        print(f"  Model Identifier:     {model}")

        if not configured and not allow_simulated:
            print("\n[STATUS: BLOCKED] Remote backend has not configured NEBIUS_API_KEY.")
            print("  [EXIT] Exiting with status 2 (BLOCKED: Remote provider unconfigured).")
            return 2

        # 2. Authenticate an ephemeral test session
        print("\n[2/3] Authenticating Ephemeral Session with Remote Backend...")
        ts = int(time.time())
        reg_payload = {
            "email": f"test_nebius_{ts}@synapse.internal",
            "username": f"nebius_test_{ts}",
            "password": "SecurePassword123!",
            "full_name": "Nebius Live Verifier",
        }
        headers = {"Origin": "https://synapseos-three.vercel.app"}
        reg_res = await client.post(
            f"{clean_url}/api/v1/auth/register",
            json=reg_payload,
            headers=headers,
        )
        if reg_res.status_code not in (200, 201):
            print(f"[STATUS: FAILED] Remote user registration returned HTTP {reg_res.status_code}: {reg_res.text}")
            return 1

        user_data = reg_res.json()
        workspace_id = user_data.get("default_workspace_id")
        if not workspace_id:
            ws_res = await client.post(
                f"{clean_url}/api/v1/workspaces",
                json={"name": "Nebius Live Workspace", "description": "Verification Workspace"},
                headers=headers,
            )
            if ws_res.status_code in (200, 201):
                workspace_id = ws_res.json().get("id")

        # 3. Seed Memory to trigger actual LLM inference path
        print("\n[3/4] Seeding Verified Memory Context to Workspace...")
        mem_payload = {
            "title": "Kernel Architecture Note",
            "content": "The SynapseOS kernel reasoning engine is actively operational with NVIDIA Nemotron architecture.",
            "memory_type": "knowledge",
            "tags": ["kernel", "architecture", "test"],
            "importance_score": 0.9,
        }
        mem_res = await client.post(
            f"{clean_url}/api/v1/memory?workspace_id={workspace_id}",
            json=mem_payload,
            headers=headers,
        )
        if mem_res.status_code not in (200, 201):
            print(f"[STATUS: FAILED] Failed to seed memory: {mem_res.text}")
            return 1

        # 4. Dispatch RAG Query to deployed backend
        print("\n[4/4] Dispatching RAG Query to Deployed Backend...")
        rag_payload = {
            "query": "What is the operational status of the SynapseOS kernel reasoning engine?",
            "workspace_id": workspace_id,
        }
        start_time = time.perf_counter()
        rag_res = await client.post(
            f"{clean_url}/api/v1/rag/query",
            json=rag_payload,
            headers=headers,
            timeout=30.0,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if rag_res.status_code != 200:
            print(f"[STATUS: FAILED] Remote RAG query returned HTTP {rag_res.status_code}: {rag_res.text}")
            return 1

        data = rag_res.json()
        is_simulated = data.get("is_simulated", True)
        provider = data.get("provider", "unknown")
        model_used = data.get("model_used", "unknown")
        confidence = data.get("confidence_score", data.get("confidence", 0.0))
        citations = len(data.get("citations", []))

        print("\n  Response Attributes:")
        print(f"  Model Used:       {model_used}")
        print(f"  Provider:         {provider}")
        print(f"  Is Simulated:     {is_simulated}")
        print(f"  Confidence:       {confidence}")
        print(f"  Citations Count:  {citations}")
        print(f"  Roundtrip Time:   {elapsed_ms:.1f}ms")

        # Guardrail early exit is not an LLM invocation
        if provider == "synapseos-guardrail":
            print("\n[STATUS: BLOCKED] Request abstained via guardrail without LLM inference.")
            return 1

        if is_simulated or "simulated" in provider.lower():
            if not allow_simulated:
                print("\n[STATUS: FAILED] Remote backend returned simulated response, expected live cloud inference.")
                return 1
            else:
                print("\n" + "=" * 72)
                print("   [STATUS: SIMULATION_VERIFIED]")
                print("   Remote backend is operating with honest, verified simulation mode.")
                print("=" * 72 + "\n")
                return 0

        print("\n" + "=" * 72)
        print("   [STATUS: LIVE_PROVIDER_VERIFIED]")
        print("   Live authenticated remote inference verified through deployed SynapseOS!")
        print("=" * 72 + "\n")
        return 0

async def verify_nebius(api_key: str | None = None, allow_simulated: bool = False) -> int:
    """Verify live inference directly against Nebius Token Factory."""
    print("=" * 72)
    print("   NEBIUS TOKEN FACTORY & NVIDIA NEMOTRON LIVE VERIFICATION")
    print("=" * 72)

    resolved_key = api_key or os.environ.get("NEBIUS_API_KEY") or settings.nebius_api_key
    base_url = settings.nebius_base_url
    model = settings.nebius_model

    print(f"\n[1/4] Inspecting Provider Configuration:")
    print(f"  Endpoint Base URL: {base_url}")
    print(f"  Target Model ID:   {model}")
    print(f"  API Key Status:    {mask_key(resolved_key)}")
    print(f"  Require Live Call: {not allow_simulated}")

    client = NebiusNemotronClient(
        api_key=resolved_key,
        base_url=base_url,
        model=model,
    )

    if not client.is_configured:
        print("\n[STATUS: BLOCKED] Credentials unconfigured.")
        print("  NEBIUS_API_KEY is not set or contains a placeholder value.")
        print("\n  Steps to configure your Nebius promotional credits:")
        print("  1. Sign in to Nebius Token Factory at: https://tokenfactory.nebius.com/")
        print("  2. Open the profile menu in the top-right corner and select 'Top Up'.")
        print("  3. Enter your promotional code to redeem the 25 credit balance.")
        print("  4. Verify your promotional balance in the dashboard.")
        print("  5. Navigate to 'API Keys', generate an API key, and copy it.")
        print("  6. Set the key in your local .env file:")
        print("     NEBIUS_API_KEY=\"your_actual_key_here\"")
        print("     NEBIUS_MODEL=\"nvidia/Llama-3.1-Nemotron-70B-Instruct-HF\"")
        print("  7. Re-run this verification script:")
        print("     python scripts/verify_nebius_inference.py\n")

        if allow_simulated:
            print("  [INFO] --allow-simulated flag was provided. Running offline simulation test...")
        else:
            print("  [EXIT] Exiting with status 2 (BLOCKED: Credentials unconfigured).")
            return 2

    print(f"\n[2/4] Testing Health Endpoint (GET {base_url}/models)...")
    health = await client.health_check()
    print(f"  Health Check Status: {health.get('status')} (configured={health.get('configured')})")
    if health.get("status") == "auth_error":
        print("\n[STATUS: BLOCKED] Authentication failed: Nebius Token Factory returned 401/403.")
        print("  Your NEBIUS_API_KEY is invalid, expired, or has insufficient permissions.")
        return 1

    print("\n[3/4] Dispatching Minimal Verification Prompt to Model...")
    test_messages = [
        {"role": "system", "content": "You are an AI system health check. Respond strictly with 'OK'."},
        {"role": "user", "content": "Respond with single word: OK"},
    ]

    try:
        start_time = time.perf_counter()
        response = await client.chat_completion(
            messages=test_messages,
            temperature=0.0,
            max_tokens=16,
            allow_fallback=allow_simulated,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        print(f"\n[4/4] Validating Response Payload:")
        print(f"  Response Content: \"{response.content.strip()}\"")
        print(f"  Reported Model:   {response.model}")
        print(f"  Provider:         {response.provider}")
        print(f"  Is Simulated:     {response.is_simulated}")
        print(f"  Roundtrip Time:   {response.usage.latency_ms:.1f}ms (Measured: {elapsed_ms:.1f}ms)")
        print(f"  Tokens Used:      prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}")

        if response.is_simulated:
            if not allow_simulated:
                print("\n[STATUS: FAILED] Expected live cloud inference but received simulated response.")
                return 1
            else:
                print("\n" + "=" * 72)
                print("   [STATUS: SIMULATION_VERIFIED]")
                print("   Deterministic offline simulation completed successfully.")
                print("   CRITICAL NOTICE: This confirms offline simulation only.")
                print("   A passing simulation test is NOT live-provider verification.")
                print("=" * 72 + "\n")
                return 0

        print("\n" + "=" * 72)
        print("   [STATUS: LIVE_PROVIDER_VERIFIED]")
        print("   Live Nebius Token Factory NVIDIA Nemotron inference verified successfully!")
        print("=" * 72 + "\n")
        return 0

    except Exception as e:
        print(f"\n[STATUS: FAILED] Live inference request failed:")
        print(f"  Error Type:    {type(e).__name__}")
        print(f"  Error Message: {str(e)}")
        print("\n  Diagnostic guidance:")
        print("  - If 401/403: Verify that NEBIUS_API_KEY in .env matches your active Nebius key.")
        print("  - If 402/429: Check account credit balance at https://tokenfactory.nebius.com/")
        print("  - If 404: The model name may differ. Check available models via: GET /models")
        print("  - If Timeout: Nebius cluster may be experiencing high demand; consider increasing NEBIUS_TIMEOUT_SECONDS.")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Verify Nebius Token Factory inference connectivity.")
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Nebius Token Factory API key override",
    )
    parser.add_argument(
        "--remote-url",
        type=str,
        default=None,
        help="Target deployed SynapseOS backend URL (e.g. https://synapseos-api-2onj.onrender.com)",
    )
    parser.add_argument(
        "--allow-simulated",
        action="store_true",
        help="Allow local simulation fallback if API credentials are not set",
    )
    args = parser.parse_args()

    if args.remote_url:
        exit_code = asyncio.run(verify_remote_backend(remote_url=args.remote_url, allow_simulated=args.allow_simulated))
    else:
        exit_code = asyncio.run(verify_nebius(api_key=args.api_key, allow_simulated=args.allow_simulated))

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
