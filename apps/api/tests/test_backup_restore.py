"""Automated smoke and regression tests for SynapseOS Backup & Recovery."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.backup_restore import (
    calculate_sha256,
    create_backup,
    restore_backup,
    verify_backup,
)


@pytest.fixture
def mock_data_env():
    """Create a temporary populated data directory and backup directory."""
    temp_dir = tempfile.mkdtemp(prefix="synapse_test_data_")
    backup_dir = tempfile.mkdtemp(prefix="synapse_test_backups_")
    restore_dir = tempfile.mkdtemp(prefix="synapse_test_restore_")

    data_path = Path(temp_dir)
    # Populate mock files simulating local SQLite db, vectors, graph, approvals
    (data_path / "synapseos_local.db").write_text("SQLite format 3\x00mock_database_content", encoding="utf-8")
    (data_path / "local_vector_store.json").write_text(
        json.dumps({"mem_1": {"vector": [0.1, 0.2, 0.3], "payload": {"memory_id": "1"}}}),
        encoding="utf-8",
    )
    (data_path / "local_graph_store.json").write_text(
        json.dumps({"nodes": {"n1": {"title": "Node 1"}}, "relationships": []}),
        encoding="utf-8",
    )
    (data_path / "approval_sessions.json").write_text(
        json.dumps({"sess_1": {"status": "awaiting_approval", "goal": "Deploy app"}}),
        encoding="utf-8",
    )

    yield {
        "data_dir": data_path,
        "backup_dir": Path(backup_dir),
        "restore_dir": Path(restore_dir),
    }

    shutil.rmtree(temp_dir, ignore_errors=True)
    shutil.rmtree(backup_dir, ignore_errors=True)
    shutil.rmtree(restore_dir, ignore_errors=True)


def test_backup_creation_and_verification(mock_data_env):
    """Test that create_backup archives all files and verify_backup confirms integrity."""
    data_dir = mock_data_env["data_dir"]
    backup_dir = mock_data_env["backup_dir"]

    archive = create_backup(data_dir=data_dir, output_dir=backup_dir)
    assert archive.exists()
    assert archive.stat().st_size > 0

    res = verify_backup(archive)
    assert res["valid"] is True
    assert len(res["errors"]) == 0
    manifest = res["manifest"]
    assert manifest["total_files"] == 4
    file_names = [f["rel_path"] for f in manifest["files"]]
    assert "synapseos_local.db" in file_names
    assert "local_vector_store.json" in file_names
    assert "local_graph_store.json" in file_names
    assert "approval_sessions.json" in file_names


def test_verify_detects_tampering(mock_data_env):
    """Test that tampering with archive contents is detected by SHA-256 verification."""
    data_dir = mock_data_env["data_dir"]
    backup_dir = mock_data_env["backup_dir"]

    archive = create_backup(data_dir=data_dir, output_dir=backup_dir)

    # Corrupt the archive bytes
    with open(archive, "r+b") as f:
        f.seek(100)
        f.write(b"CORRUPTED_BYTES_HERE")

    res = verify_backup(archive)
    assert res["valid"] is False
    assert len(res["errors"]) > 0


def test_restore_backup_recovers_files(mock_data_env):
    """Test that restore_backup unpacks files cleanly and verifies content equivalence."""
    data_dir = mock_data_env["data_dir"]
    backup_dir = mock_data_env["backup_dir"]
    restore_dir = mock_data_env["restore_dir"]

    archive = create_backup(data_dir=data_dir, output_dir=backup_dir)

    # Restore into fresh directory
    result = restore_backup(
        archive_path=archive,
        target_data_dir=restore_dir,
        create_safety_snapshot=False,
    )

    assert result["status"] == "success"
    assert result["restored_count"] == 4

    restored_db = restore_dir / "synapseos_local.db"
    assert restored_db.exists()
    assert restored_db.read_text(encoding="utf-8") == "SQLite format 3\x00mock_database_content"

    restored_vectors = json.loads((restore_dir / "local_vector_store.json").read_text(encoding="utf-8"))
    assert "mem_1" in restored_vectors

    restored_graph = json.loads((restore_dir / "local_graph_store.json").read_text(encoding="utf-8"))
    assert "n1" in restored_graph["nodes"]


def test_restore_creates_safety_snapshot(mock_data_env):
    """Test that restoring over existing files creates an automatic safety snapshot."""
    data_dir = mock_data_env["data_dir"]
    backup_dir = mock_data_env["backup_dir"]

    archive = create_backup(data_dir=data_dir, output_dir=backup_dir)

    # Restore over original data_dir
    result = restore_backup(
        archive_path=archive,
        target_data_dir=data_dir,
        create_safety_snapshot=True,
    )

    assert result["status"] == "success"
    assert result["safety_snapshot"] is not None
    assert Path(result["safety_snapshot"]).exists()
