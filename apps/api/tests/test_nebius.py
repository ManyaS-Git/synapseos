"""Tests for Nebius Token Factory & NVIDIA Nemotron integration."""

import os
from unittest.mock import patch, AsyncMock
import pytest
import httpx
from pydantic import BaseModel

from app.core.llm.nebius import NebiusNemotronClient, LLMResponse, LLMUsage


class SamplePlan(BaseModel):
    goal: str
    reasoning: str
    confidence_score: float


@pytest.mark.asyncio
async def test_nebius_client_init():
    """Client initializes with default settings."""
    client = NebiusNemotronClient(
        api_key="",
        base_url="https://api.tokenfactory.nebius.com/v1",
        model="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    )
    assert not client.is_configured
    assert client.base_url == "https://api.tokenfactory.nebius.com/v1"
    assert "Nemotron" in client.model


@pytest.mark.asyncio
async def test_nebius_simulated_completion():
    """Client provides valid LLMResponse in simulated mode without API key."""
    client = NebiusNemotronClient(api_key="")
    messages = [
        {"role": "system", "content": "You are SynapseOS assistant."},
        {"role": "user", "content": "What is the status of my workspace?"},
    ]
    resp = await client.chat_completion(messages)
    assert isinstance(resp, LLMResponse)
    assert resp.content
    assert resp.is_simulated is True
    assert resp.usage.latency_ms >= 0
    assert "Nemotron" in resp.model


@pytest.mark.asyncio
async def test_nebius_structured_completion():
    """Client returns validated Pydantic model for structured output requests."""
    client = NebiusNemotronClient(api_key="")
    messages = [
        {"role": "user", "content": "Generate a plan for setting up project memory with schema AgentPlan"},
    ]
    plan, resp = await client.structured_completion(messages, SamplePlan)
    assert isinstance(plan, SamplePlan)
    assert plan.goal
    assert plan.confidence_score > 0
    assert resp.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_nebius_health_check_mock_mode():
    """Health check reports ready in mock/offline mode when unconfigured."""
    client = NebiusNemotronClient(api_key="")
    health = await client.health_check()
    assert health["provider"] == "nebius-token-factory"
    assert not health["configured"]


@pytest.mark.asyncio
async def test_nebius_mocked_success():
    """Mocked live 200 OK response from Nebius Token Factory."""
    client = NebiusNemotronClient(api_key="mock-valid-key")
    messages = [{"role": "user", "content": "Ping"}]

    mock_resp_data = {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Pong from NVIDIA Nemotron"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 6,
            "total_tokens": 11,
        },
    }

    mock_response = httpx.Response(
        status_code=200,
        json=mock_resp_data,
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        resp = await client.chat_completion(messages, allow_fallback=False)

        assert isinstance(resp, LLMResponse)
        assert resp.content == "Pong from NVIDIA Nemotron"
        assert resp.is_simulated is False
        assert resp.is_fallback is False
        assert resp.provider == "nebius-token-factory"
        assert resp.usage.total_tokens == 11
        assert resp.usage.prompt_tokens == 5
        assert resp.usage.completion_tokens == 6


@pytest.mark.asyncio
async def test_nebius_mocked_401_auth_error():
    """Mocked 401 Unauthorized stops retrying immediately and raises or falls back."""
    client = NebiusNemotronClient(api_key="mock-invalid-key")
    messages = [{"role": "user", "content": "Hello"}]

    mock_response = httpx.Response(
        status_code=401,
        json={"error": {"message": "Invalid API Key"}},
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        # When allow_fallback=False, strict failure is raised
        with pytest.raises(RuntimeError, match="Live Nebius inference failed"):
            await client.chat_completion(messages, allow_fallback=False)

        # 401 should NOT retry: called exactly once
        assert mock_post.call_count == 1

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        # When allow_fallback=True, graceful fallback is applied
        resp = await client.chat_completion(messages, allow_fallback=True)
        assert resp.is_simulated is True
        assert resp.is_fallback is True
        assert "fallback" in resp.provider


@pytest.mark.asyncio
async def test_nebius_mocked_404_model_not_found():
    """Mocked 404 Model Not Found aborts retries without endless looping."""
    client = NebiusNemotronClient(api_key="mock-key", model="non-existent-model")
    messages = [{"role": "user", "content": "Hello"}]

    mock_response = httpx.Response(
        status_code=404,
        json={"error": {"message": "Model not found"}},
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(RuntimeError, match="Live Nebius inference failed"):
            await client.chat_completion(messages, allow_fallback=False)

        # 404 should abort without retries
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_nebius_mocked_429_rate_limit_retry():
    """Mocked 429 Rate Limit retries transient error and succeeds."""
    client = NebiusNemotronClient(api_key="mock-key")
    messages = [{"role": "user", "content": "Hello"}]

    mock_429 = httpx.Response(
        status_code=429,
        json={"error": {"message": "Rate limit reached"}},
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )
    mock_200 = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": "Recovered after rate limit"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 5, "total_tokens": 7},
        },
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_post.side_effect = [mock_429, mock_200]
        resp = await client.chat_completion(messages, allow_fallback=False)

        assert mock_post.call_count == 2
        assert mock_sleep.call_count == 1
        assert resp.content == "Recovered after rate limit"
        assert resp.is_simulated is False


@pytest.mark.asyncio
async def test_nebius_mocked_timeout_retry():
    """Mocked timeout retries and succeeds on subsequent attempt."""
    client = NebiusNemotronClient(api_key="mock-key")
    messages = [{"role": "user", "content": "Hello"}]

    mock_200 = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": "Recovered after timeout"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 4, "total_tokens": 6},
        },
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_post.side_effect = [
            httpx.TimeoutException("Read timeout", request=httpx.Request("POST", "http://test")),
            mock_200,
        ]
        resp = await client.chat_completion(messages, allow_fallback=False)

        assert mock_post.call_count == 2
        assert mock_sleep.call_count == 1
        assert resp.content == "Recovered after timeout"


@pytest.mark.asyncio
async def test_nebius_mocked_structured_output_json_fenced():
    """Client extracts valid JSON from markdown code fences in live model response."""
    client = NebiusNemotronClient(api_key="mock-key")
    messages = [{"role": "user", "content": "Plan project"}]

    fenced_content = """Here is the structured plan you requested:
```json
{
  "goal": "Build SynapseOS Mobile App",
  "reasoning": "User requested mobile app planning.",
  "confidence_score": 0.98
}
```
Let me know if you need revisions.
"""

    mock_200 = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": fenced_content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 40, "total_tokens": 50},
        },
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_200
        plan, resp = await client.structured_completion(messages, SamplePlan, allow_fallback=False)

        assert isinstance(plan, SamplePlan)
        assert plan.goal == "Build SynapseOS Mobile App"
        assert plan.confidence_score == 0.98
        assert resp.is_simulated is False


@pytest.mark.asyncio
async def test_nebius_privacy_mode_local_only_blocks_egress():
    """When PRIVACY_MODE=local_only, no remote network requests are attempted."""
    client = NebiusNemotronClient(api_key="mock-secret-key", privacy_mode="local_only")
    messages = [{"role": "user", "content": "Process confidential data"}]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        resp = await client.chat_completion(messages)

        # httpx post must NOT be called at all
        assert mock_post.call_count == 0
        assert resp.is_simulated is True
        assert resp.provider == "local-simulation (privacy:local_only)"


@pytest.mark.asyncio
async def test_nebius_no_api_key_leakage_in_error_message():
    """Ensure secret API key never appears in exceptions or error strings."""
    secret = "sk-super-secret-key-12345"
    client = NebiusNemotronClient(api_key=secret)
    messages = [{"role": "user", "content": "Fail"}]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Simulate connection error with string containing the key
        mock_post.side_effect = httpx.ConnectError(f"Connection failed to endpoint using {secret}")

        with pytest.raises(RuntimeError) as exc_info:
            await client.chat_completion(messages, allow_fallback=False)

        err_text = str(exc_info.value)
        assert secret not in err_text
        assert "[REDACTED_API_KEY]" in err_text


@pytest.mark.asyncio
async def test_nebius_malformed_json_fallback_repair():
    """Malformed JSON from remote provider falls back cleanly without crashing."""
    client = NebiusNemotronClient(api_key="mock-key")
    messages = [{"role": "user", "content": "Plan something"}]

    # Return completely invalid JSON from provider
    mock_200 = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": "Not JSON at all: error in syntax {[[["}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        },
        request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_200
        # With allow_fallback=True (default), it recovers with simulated plan
        plan, resp = await client.structured_completion(messages, SamplePlan, allow_fallback=True)
        assert isinstance(plan, SamplePlan)
        assert plan.goal

        # With allow_fallback=False, it raises ValueError cleanly
        mock_post.return_value = mock_200
        with pytest.raises(ValueError, match="Failed to validate response against SamplePlan"):
            await client.structured_completion(messages, SamplePlan, allow_fallback=False)


@pytest.mark.asyncio
async def test_nebius_telemetry_recording():
    """Client records metrics via LLMTelemetryManager on both live calls and fallbacks."""
    from app.core.llm.telemetry import llm_telemetry

    initial_count = llm_telemetry.get_summary()["total_calls"]
    client = NebiusNemotronClient(api_key="")
    await client.chat_completion([{"role": "user", "content": "Test telemetry"}])

    summary = llm_telemetry.get_summary()
    assert summary["total_calls"] == initial_count + 1
    assert summary["simulated_calls"] >= 1
    assert "simulated" in summary["recent_events"][-1]["provider"]


@pytest.mark.asyncio
async def test_real_nebius_if_configured():
    """Real integration test against Nebius Token Factory if NEBIUS_API_KEY is supplied."""
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        pytest.skip("NEBIUS_API_KEY not set in environment, skipping live API test")

    client = NebiusNemotronClient(api_key=key)
    messages = [{"role": "user", "content": "Say hello from SynapseOS!"}]
    resp = await client.chat_completion(messages, max_tokens=20)
    assert isinstance(resp, LLMResponse)
    assert resp.provider == "nebius-token-factory"
    assert resp.usage.total_tokens > 0

