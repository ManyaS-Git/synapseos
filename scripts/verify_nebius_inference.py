"""
Repeatable Nebius Token Factory Live Inference Verification CLI
===============================================================
Verifies real-time connectivity and inference with NVIDIA Nemotron models
hosted on Nebius Token Factory without exposing sensitive keys or prompts.

Usage:
    python scripts/verify_nebius_inference.py
    python scripts/verify_nebius_inference.py --allow-simulated
"""

import sys
import os
import argparse
import asyncio
import time

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

async def verify_nebius(allow_simulated: bool = False) -> int:
    print("=" * 72)
    print("   NEBIUS TOKEN FACTORY & NVIDIA NEMOTRON LIVE VERIFICATION")
    print("=" * 72)

    api_key = settings.nebius_api_key
    base_url = settings.nebius_base_url
    model = settings.nebius_model

    print(f"\n[1/4] Inspecting Provider Configuration:")
    print(f"  Endpoint Base URL: {base_url}")
    print(f"  Target Model ID:   {model}")
    print(f"  API Key Status:    {mask_key(api_key)}")
    print(f"  Require Live Call: {not allow_simulated}")

    client = NebiusNemotronClient(
        api_key=api_key,
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
        "--allow-simulated",
        action="store_true",
        help="Allow local simulation fallback if API credentials are not set",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(verify_nebius(allow_simulated=args.allow_simulated))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
