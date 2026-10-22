"""Unit tests for document upload and ingestion endpoint."""

import io
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User
from app.models.memory import Memory, MemoryType, MemoryStatus


@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(),
        email="docuser@synapseos.local",
        username="docuser",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_upload_text_document_success(mock_user):
    """Uploading a markdown document extracts text, chunks it, and creates memory."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()
    doc_content = b"# Architecture Overview\n\nSynapseOS uses modular monolith architecture with FastAPI."

    upload_file = UploadFile(
        file=io.BytesIO(doc_content),
        filename="system_architecture.md",
        headers={"content-type": "text/markdown"},
    )

    created_mem = Memory(
        id=uuid.uuid4(),
        owner_id=mock_user.id,
        workspace_id=ws_id,
        title="System Architecture",
        content=doc_content.decode("utf-8"),
        memory_type=MemoryType.KNOWLEDGE,
        source="system_architecture.md",
        status=MemoryStatus.ACTIVE,
        importance_score=0.7,
        confidence=1.0,
    )

    with patch("app.services.memory.memory.MemoryService.create_memory", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = created_mem

        res = await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags="arch,docs",
            current_user=mock_user,
            db=mock_db,
        )

        assert res["title"] == "System Architecture"
        assert res["source"] == "system_architecture.md"
        mock_create.assert_called_once()
        mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_unsupported_format_fails(mock_user):
    """Uploading an unsupported format raises 400 error."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile, HTTPException

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()

    upload_file = UploadFile(
        file=io.BytesIO(b"\x7fELF\x02\x01\x01"),
        filename="binary_executable.bin",
    )

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags=None,
            current_user=mock_user,
            db=mock_db,
        )

    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_empty_file_fails(mock_user):
    """Uploading an empty file raises 400 error."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile, HTTPException

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()

    upload_file = UploadFile(
        file=io.BytesIO(b"   "),
        filename="empty.txt",
    )

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags=None,
            current_user=mock_user,
            db=mock_db,
        )

    assert exc_info.value.status_code == 400
    assert "contains no extractable text" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_json_document_success(mock_user):
    """Uploading a valid JSON file parses syntax and preserves structure."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()
    json_bytes = b'{"system": "SynapseOS", "version": "1.0.0", "provider": "Nebius"}'

    upload_file = UploadFile(
        file=io.BytesIO(json_bytes),
        filename="system_config.json",
        headers={"content-type": "application/json"},
    )

    created_mem = Memory(
        id=uuid.uuid4(),
        owner_id=mock_user.id,
        workspace_id=ws_id,
        title="System Config",
        content=json_bytes.decode("utf-8"),
        memory_type=MemoryType.KNOWLEDGE,
        source="system_config.json",
        status=MemoryStatus.ACTIVE,
    )

    with patch("app.services.memory.memory.MemoryService.create_memory", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = created_mem

        res = await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags="config,json",
            current_user=mock_user,
            db=mock_db,
        )

        assert res["title"] == "System Config"
        assert res["source"] == "system_config.json"
        mock_create.assert_called_once()
        # Verify content passed to create_memory was structured JSON
        _, kwargs = mock_create.call_args
        assert '"version": "1.0.0"' in kwargs["content"]


@pytest.mark.asyncio
async def test_upload_invalid_json_fails(mock_user):
    """Uploading malformed JSON fails with 400 and syntax error detail."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile, HTTPException

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()

    upload_file = UploadFile(
        file=io.BytesIO(b'{"unclosed": "json'),
        filename="broken.json",
    )

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags=None,
            current_user=mock_user,
            db=mock_db,
        )

    assert exc_info.value.status_code == 400
    assert "Invalid JSON syntax" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_csv_document_success(mock_user):
    """Uploading a valid CSV file reads rows and ingests content."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()
    csv_bytes = b"feature,status,priority\nPersistent Memory,Active,High\nRAG Citations,Active,High\n"

    upload_file = UploadFile(
        file=io.BytesIO(csv_bytes),
        filename="roadmap.csv",
        headers={"content-type": "text/csv"},
    )

    created_mem = Memory(
        id=uuid.uuid4(),
        owner_id=mock_user.id,
        workspace_id=ws_id,
        title="Roadmap",
        content=csv_bytes.decode("utf-8"),
        memory_type=MemoryType.KNOWLEDGE,
        source="roadmap.csv",
        status=MemoryStatus.ACTIVE,
    )

    with patch("app.services.memory.memory.MemoryService.create_memory", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = created_mem

        res = await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags="csv,planning",
            current_user=mock_user,
            db=mock_db,
        )

        assert res["title"] == "Roadmap"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_upload_empty_csv_fails(mock_user):
    """Uploading an empty CSV raises 400."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile, HTTPException

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()

    upload_file = UploadFile(
        file=io.BytesIO(b"   \n\n"),
        filename="empty.csv",
    )

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags=None,
            current_user=mock_user,
            db=mock_db,
        )

    assert exc_info.value.status_code == 400
    assert "CSV file is empty" in exc_info.value.detail or "contains no readable data rows" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_scanned_pdf_without_ocr_fails(mock_user):
    """Uploading a PDF with zero extractable text raises an explicit OCR unsupported message."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile, HTTPException

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()

    # Mock pypdf reader returning an empty page
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    upload_file = UploadFile(
        file=io.BytesIO(b"%PDF-1.4 mock data"),
        filename="scanned_receipt.pdf",
    )

    with patch("pypdf.PdfReader", return_value=mock_reader):
        with pytest.raises(HTTPException) as exc_info:
            await upload_document(
                file=upload_file,
                workspace_id=ws_id,
                project_id=None,
                memory_type="knowledge",
                tags=None,
                current_user=mock_user,
                db=mock_db,
            )

    assert exc_info.value.status_code == 400
    assert "OCR is not supported" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_valid_pdf_extracts_text(mock_user):
    """Uploading a PDF with valid text extracts content into pages."""
    from app.routers.v1.memory import upload_document
    from fastapi import UploadFile

    mock_db = AsyncMock()
    ws_id = uuid.uuid4()

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "SynapseOS Whitepaper Page 1 text"

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    upload_file = UploadFile(
        file=io.BytesIO(b"%PDF-1.4 mock data"),
        filename="whitepaper.pdf",
    )

    created_mem = Memory(
        id=uuid.uuid4(),
        owner_id=mock_user.id,
        workspace_id=ws_id,
        title="Whitepaper",
        content="--- Page 1 ---\nSynapseOS Whitepaper Page 1 text",
        memory_type=MemoryType.KNOWLEDGE,
        source="whitepaper.pdf",
        status=MemoryStatus.ACTIVE,
    )

    with patch("pypdf.PdfReader", return_value=mock_reader), \
         patch("app.services.memory.memory.MemoryService.create_memory", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = created_mem

        res = await upload_document(
            file=upload_file,
            workspace_id=ws_id,
            project_id=None,
            memory_type="knowledge",
            tags="pdf,research",
            current_user=mock_user,
            db=mock_db,
        )

        assert res["title"] == "Whitepaper"
        mock_create.assert_called_once()
