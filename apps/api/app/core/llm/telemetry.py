"""Privacy-Conscious LLM Observability & Telemetry for SynapseOS.

Tracks operational metrics for LLM inference (latency, token usage, retry counts,
provider selection, simulation/fallback flags, and correlation IDs) while strictly
excluding sensitive user prompts, completions, and API keys.
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Any

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger("synapseos.llm.telemetry")


class LLMTelemetryEvent(BaseModel):
    """Structured telemetry event for a single LLM invocation."""
    request_id: str
    timestamp: float = Field(default_factory=time.time)
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retries: int = 0
    success: bool = True
    is_simulated: bool = False
    is_fallback: bool = False
    status_code: int | None = None
    error_type: str | None = None


class LLMTelemetryManager:
    """Manages operational telemetry and usage metrics for LLM providers."""

    def __init__(self, max_history: int = 100) -> None:
        self._max_history = max_history
        self._history: deque[LLMTelemetryEvent] = deque(maxlen=max_history)
        self._total_requests: int = 0
        self._successful_requests: int = 0
        self._failed_requests: int = 0
        self._simulated_requests: int = 0
        self._fallback_requests: int = 0
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._total_tokens: int = 0
        self._total_latency_ms: float = 0.0

    def record_call(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        retries: int = 0,
        success: bool = True,
        is_simulated: bool = False,
        is_fallback: bool = False,
        status_code: int | None = None,
        error_type: str | None = None,
        request_id: str | None = None,
    ) -> LLMTelemetryEvent:
        """Record an LLM call event and update aggregated telemetry counters."""
        if not request_id:
            try:
                cv = structlog.contextvars.get_contextvars()
                request_id = cv.get("request_id") or f"req-{uuid.uuid4().hex[:8]}"
            except Exception:
                request_id = f"req-{uuid.uuid4().hex[:8]}"

        event = LLMTelemetryEvent(
            request_id=request_id,
            timestamp=time.time(),
            provider=provider,
            model=model,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            retries=retries,
            success=success,
            is_simulated=is_simulated,
            is_fallback=is_fallback,
            status_code=status_code,
            error_type=error_type,
        )

        self._history.append(event)
        self._total_requests += 1

        if success:
            self._successful_requests += 1
        else:
            self._failed_requests += 1

        if is_simulated:
            self._simulated_requests += 1

        if is_fallback:
            self._fallback_requests += 1

        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens
        self._total_tokens += total_tokens
        self._total_latency_ms += latency_ms

        logger.debug(
            "Recorded LLM telemetry event",
            provider=provider,
            model=model,
            latency_ms=event.latency_ms,
            total_tokens=event.total_tokens,
            is_simulated=is_simulated,
            is_fallback=is_fallback,
            success=success,
        )
        return event

    def get_summary(self) -> dict[str, Any]:
        """Get aggregate usage metrics and recent invocation history."""
        avg_latency = (
            round(self._total_latency_ms / self._total_requests, 2)
            if self._total_requests > 0
            else 0.0
        )
        return {
            "total_calls": self._total_requests,
            "simulated_calls": self._simulated_requests,
            "metrics": {
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "failed_requests": self._failed_requests,
                "simulated_requests": self._simulated_requests,
                "fallback_requests": self._fallback_requests,
                "total_prompt_tokens": self._total_prompt_tokens,
                "total_completion_tokens": self._total_completion_tokens,
                "total_tokens": self._total_tokens,
                "avg_latency_ms": avg_latency,
            },
            "recent_events": [e.model_dump() for e in reversed(self._history)],
        }

    def reset(self) -> None:
        """Reset counters and clear history (useful for isolated tests)."""
        self._history.clear()
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._simulated_requests = 0
        self._fallback_requests = 0
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0


# Global singleton manager
llm_telemetry = LLMTelemetryManager()
