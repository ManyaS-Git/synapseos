"""Evidence-backed Retrieval-Augmented Generation (RAG) Pipeline for SynapseOS.

Core guarantees:
1. Retrieval is strictly bounded to the authenticated workspace.
2. Every generated response includes verifiable source citations.
3. Explicit abstention when evidence is insufficient or contradictory.
4. Powered by NVIDIA Nemotron via Nebius Token Factory.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.llm.nebius import nebius_client
from app.models.memory import MemoryStatus
from app.repositories.memory import MemoryRepository
from app.services.memory.embedding import embedding_service
from app.services.memory.vector_store import VectorStore

logger = structlog.get_logger("synapseos.rag")


class RAGCitation(BaseModel):
    """Source reference for evidence attribution."""
    citation_index: int
    memory_id: str
    title: str
    chunk_index: int = 0
    excerpt: str
    similarity_score: float
    memory_type: str = "knowledge"
    source: str | None = None
    source_url: str | None = None


class RAGQueryRequest(BaseModel):
    """RAG query parameters."""
    query: str = Field(..., min_length=1, max_length=1000)
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.25, ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    """Evidence-backed answer response."""
    model_config = {"protected_namespaces": ()}

    query: str
    answer: str
    citations: list[RAGCitation]
    is_unsupported: bool = False
    confidence_score: float
    model_used: str
    latency_ms: float
    provider: str
    is_simulated: bool = False


class RAGPipeline:
    """Orchestrates evidence retrieval, abstention verification, and Nemotron generation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.vector_store = VectorStore()

    async def execute(self, req: RAGQueryRequest) -> RAGQueryResponse:
        """Execute the RAG query with evidence grounding and citation tracking."""
        start_time = time.perf_counter()

        # 1. Generate query embedding
        query_embedding = await embedding_service.generate_embedding(req.query)

        # 2. Retrieve candidate chunks from vector store
        filters = {"workspace_id": str(req.workspace_id)}
        if req.project_id:
            filters["project_id"] = str(req.project_id)

        vector_hits = await self.vector_store.search(
            embedding=query_embedding,
            top_k=req.top_k * 2,
            filters=filters,
        )

        # 3. Assemble and rank citations from persistent memory
        citations: list[RAGCitation] = []
        seen_memories = set()

        for hit in vector_hits:
            score = float(hit.get("score", 0.0))
            if score < req.min_score:
                continue

            payload = hit.get("payload", {})
            mid_str = payload.get("memory_id")
            if not mid_str:
                continue

            try:
                mem_uuid = uuid.UUID(mid_str)
            except ValueError:
                continue

            # Fetch authoritative memory model to verify active status & workspace ownership
            memory = await self.memory_repo.get_by_id(mem_uuid)
            if not memory or memory.status != MemoryStatus.ACTIVE:
                continue
            if memory.workspace_id != req.workspace_id:
                continue

            chunk_content = payload.get("content") or memory.content
            excerpt = chunk_content[:300].strip()

            c_index = len(citations) + 1
            citations.append(
                RAGCitation(
                    citation_index=c_index,
                    memory_id=str(memory.id),
                    title=memory.title,
                    chunk_index=payload.get("chunk_index", 0),
                    excerpt=excerpt,
                    similarity_score=round(score, 3),
                    memory_type=memory.memory_type,
                    source=memory.source,
                    source_url=memory.source_url,
                )
            )
            seen_memories.add(memory.id)
            if len(citations) >= req.top_k:
                break

        # 4. Abstention Guard: if no verified evidence passes threshold, abstain
        if not citations:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return RAGQueryResponse(
                query=req.query,
                answer=(
                    "I searched your SynapseOS memory, but could not find sufficient verified evidence "
                    "to answer this question accurately. Please add relevant notes or documents to your workspace."
                ),
                citations=[],
                is_unsupported=True,
                confidence_score=0.0,
                model_used=settings.nebius_model,
                latency_ms=round(elapsed_ms, 2),
                provider="nebius-token-factory",
            )

        # 5. Build prompt with structured citations
        context_blocks = []
        for c in citations:
            context_blocks.append(
                f"[Citation {c.citation_index}] (Title: {c.title}, Type: {c.memory_type})\n{c.excerpt}"
            )
        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are SynapseOS, a privacy-first AI Operating System with evidence-backed reasoning. "
            "You MUST answer the user's question using ONLY the provided verified memory citations.\n"
            "Rules:\n"
            "1. For every factual statement, explicitly cite the relevant citation, e.g. [Citation 1].\n"
            "2. If the context contains conflicting or outdated facts, point out the discrepancy clearly.\n"
            "3. If the context does not contain enough information to answer with confidence, abstain and state: "
            "'I do not have sufficient evidence in your stored memories to answer this question.'\n"
            "4. Never invent facts, URLs, or external data not present in the citations."
        )

        user_content = (
            f"User Question: {req.query}\n\n"
            f"Verified Memory Context:\n{context_str}\n\n"
            "Provide an evidence-backed answer citing citations [Citation 1], [Citation 2] where appropriate:"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # 6. Call NVIDIA Nemotron via Nebius Token Factory
        llm_resp = await nebius_client.chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )

        # 7. Compute overall confidence score based on top retrieval score & citations count
        top_score = citations[0].similarity_score if citations else 0.0
        confidence = round(min(1.0, top_score * 0.8 + 0.2), 2)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Check if the model itself abstained in content
        is_unsupported = "do not have sufficient" in llm_resp.content.lower()

        return RAGQueryResponse(
            query=req.query,
            answer=llm_resp.content,
            citations=citations,
            is_unsupported=is_unsupported,
            confidence_score=confidence,
            model_used=llm_resp.model,
            latency_ms=round(elapsed_ms, 2),
            provider=llm_resp.provider,
            is_simulated=llm_resp.is_simulated,
        )
