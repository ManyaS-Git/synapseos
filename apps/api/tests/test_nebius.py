"""Tests for Nebius Token Factory & NVIDIA Nemotron integration."""

import os
import pytest
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
