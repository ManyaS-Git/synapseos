"""RAG query endpoints — evidence-backed answers with verifiable citations."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException
from app.core.security import get_current_active_user
from app.models.user import User
from app.rag.pipeline import RAGPipeline, RAGQueryRequest, RAGQueryResponse
from app.repositories.workspace import WorkspaceRepository

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGQueryResponse, status_code=status.HTTP_200_OK)
async def query_rag(
    body: RAGQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RAGQueryResponse:
    """Execute an evidence-backed query against workspace memories with citations."""
    workspace_repo = WorkspaceRepository(db)
    is_member = await workspace_repo.is_member(body.workspace_id, current_user.id)
    if not is_member:
        raise ForbiddenException("You are not a member of this workspace")

    pipeline = RAGPipeline(db)
    return await pipeline.execute(body)
