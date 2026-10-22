"""Tests for Evidence-backed RAG Pipeline and Abstention mechanism."""

import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.rag.pipeline import RAGPipeline, RAGQueryRequest, RAGQueryResponse, RAGCitation
from app.models.memory import Memory, MemoryStatus, MemoryType


@pytest.mark.asyncio
async def test_rag_abstains_when_no_evidence():
    """RAG pipeline must abstain when no matching memories are found."""
    mock_session = AsyncMock()
    pipeline = RAGPipeline(mock_session)

    # Mock vector store returning no hits
    pipeline.vector_store.search = AsyncMock(return_value=[])

    ws_id = uuid.uuid4()
    req = RAGQueryRequest(
        query="What is the secret deployment key?",
        workspace_id=ws_id,
        min_score=0.3,
    )

    resp = await pipeline.execute(req)
    assert isinstance(resp, RAGQueryResponse)
    assert resp.is_unsupported is True
    assert len(resp.citations) == 0
    assert "could not find sufficient" in resp.answer.lower()
    assert resp.confidence_score == 0.0


@pytest.mark.asyncio
async def test_rag_returns_citations_for_matching_evidence():
    """RAG pipeline grounds answers with verifiable citations."""
    mock_session = AsyncMock()
    pipeline = RAGPipeline(mock_session)

    ws_id = uuid.uuid4()
    mem_id = uuid.uuid4()

    mock_memory = Memory(
        id=mem_id,
        owner_id=uuid.uuid4(),
        workspace_id=ws_id,
        title="NVIDIA Hackathon Architecture",
        content="SynapseOS uses Nebius Token Factory for server-side NVIDIA Nemotron inference.",
        memory_type=MemoryType.KNOWLEDGE,
        status=MemoryStatus.ACTIVE,
        importance_score=0.9,
    )

    pipeline.vector_store.search = AsyncMock(return_value=[
        {
            "id": f"mem_{mem_id}_chunk_0",
            "score": 0.88,
            "payload": {
                "memory_id": str(mem_id),
                "workspace_id": str(ws_id),
                "content": mock_memory.content,
                "chunk_index": 0,
            },
        }
    ])
    pipeline.memory_repo.get_by_id = AsyncMock(return_value=mock_memory)

    req = RAGQueryRequest(
        query="What model does SynapseOS use?",
        workspace_id=ws_id,
        min_score=0.2,
    )

    resp = await pipeline.execute(req)
    assert isinstance(resp, RAGQueryResponse)
    assert len(resp.citations) == 1
    citation = resp.citations[0]
    assert citation.citation_index == 1
    assert citation.memory_id == str(mem_id)
    assert citation.title == "NVIDIA Hackathon Architecture"
    assert citation.similarity_score == 0.88
    assert resp.confidence_score > 0.5


@pytest.mark.asyncio
async def test_rag_enforces_workspace_isolation():
    """Memories belonging to other workspaces are strictly excluded."""
    mock_session = AsyncMock()
    pipeline = RAGPipeline(mock_session)

    ws_target = uuid.uuid4()
    ws_other = uuid.uuid4()
    mem_other = uuid.uuid4()

    # Memory in a DIFFERENT workspace
    foreign_memory = Memory(
        id=mem_other,
        owner_id=uuid.uuid4(),
        workspace_id=ws_other,
        title="Other workspace private doc",
        content="Confidential financial report of other workspace",
        memory_type=MemoryType.KNOWLEDGE,
        status=MemoryStatus.ACTIVE,
    )

    pipeline.vector_store.search = AsyncMock(return_value=[
        {
            "id": f"mem_{mem_other}_chunk_0",
            "score": 0.95,
            "payload": {
                "memory_id": str(mem_other),
                "workspace_id": str(ws_other),
                "content": foreign_memory.content,
            },
        }
    ])
    pipeline.memory_repo.get_by_id = AsyncMock(return_value=foreign_memory)

    req = RAGQueryRequest(
        query="Tell me about financial report",
        workspace_id=ws_target,
    )

    resp = await pipeline.execute(req)
    # Must abstain because the memory is NOT in ws_target
    assert resp.is_unsupported is True
    assert len(resp.citations) == 0
