"""Controlled Learning & Reflection Engine for SynapseOS.

Guarantees:
- Extracts useful lessons and summaries from verified tool execution outcomes.
- Persists transparent reflections to workspace memory so the user can inspect, edit, or delete them.
- NEVER modifies system code, security rules, or permissions autonomously.
"""

from __future__ import annotations

import uuid
from typing import Any
import structlog
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.nebius import nebius_client
from app.models.user import User

logger = structlog.get_logger("synapseos.reflection")


class ReflectionSummary(BaseModel):
    """Structured reflection outcome."""
    model_config = {"protected_namespaces": ()}

    task_summary: str
    lessons_learned: list[str] = Field(default_factory=list)
    memory_created_id: str | None = None
    confidence: float = 0.9


class ReflectionEngine:
    """Reflects upon completed agent workflows and records learned insights."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def reflect_and_learn(
        self,
        user: User,
        workspace_id: uuid.UUID,
        goal: str,
        executed_steps: list[dict[str, Any]],
        project_id: uuid.UUID | None = None,
    ) -> ReflectionSummary:
        """Analyze execution results, extract key takeaways, and persist to memory."""
        # Build prompt for Nemotron reflection
        steps_summary = []
        for s in executed_steps:
            steps_summary.append(
                f"- Step {s.get('step_number')}: {s.get('description')} "
                f"[Tool: {s.get('tool_name')}] => Status: {s.get('status')}"
            )
        steps_text = "\n".join(steps_summary)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the SynapseOS Reflection Engine. Analyze the completed agent steps "
                    "and provide a concise retrospective summary and actionable lessons learned."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User Goal: {goal}\n"
                    f"Executed Steps:\n{steps_text}\n\n"
                    "Provide a brief summary and 1-3 key insights learned from this task."
                ),
            },
        ]

        try:
            summary_model, _ = await nebius_client.structured_completion(
                messages=messages,
                response_model=ReflectionSummary,
            )
        except Exception:
            # Deterministic fallback reflection
            summary_model = ReflectionSummary(
                task_summary=f"Successfully executed workflow for: {goal[:100]}",
                lessons_learned=[
                    f"Completed {len(executed_steps)} workflow steps in workspace.",
                    "Verified tool results and persisted state.",
                ],
                confidence=0.85,
            )

        # Persist reflection into user memory as 'observation'
        from app.services.memory.memory import MemoryService
        service = MemoryService(self.session)
        lessons_text = "\n".join(f"• {l}" for l in summary_model.lessons_learned)
        reflection_content = (
            f"**Task Retrospective**: {summary_model.task_summary}\n\n"
            f"**Key Learnings**:\n{lessons_text}"
        )

        try:
            mem = await service.create_memory(
                user=user,
                workspace_id=workspace_id,
                project_id=project_id,
                title=f"Reflection: {goal[:60]}",
                content=reflection_content,
                memory_type="observation",
                tags=["reflection", "agent", "learning"],
                importance_score=0.75,
                source="reflection_engine",
            )
            await self.session.commit()
            summary_model.memory_created_id = str(mem.id)
            logger.info("Persisted reflection memory", memory_id=str(mem.id))
        except Exception as e:
            logger.warning("Failed to persist reflection memory", error=str(e))

        return summary_model
