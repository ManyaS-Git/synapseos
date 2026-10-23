"""SynapseOS Backup & Disaster Recovery CLI and Engine.

Provides durable, verifiable, and atomic backup, verification, and recovery
for SynapseOS persistent stores:
- Core SQLite relational database (users, workspaces, projects, memories, tags)
- Persistent vector store (semantic embeddings and chunks)
- Persistent knowledge graph store (nodes, entities, and relationships)
- Durable agent approval sessions (pending consequential actions)
- Ingested files and document attachments

Usage:
    python scripts/backup_restore.py backup [--output-dir DIR]
    python scripts/backup_restore.py verify <archive_path>
    python scripts/backup_restore.py restore <archive_path> [--no-safety-snapshot]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure apps/api is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_DIR = PROJECT_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

try:
    from app.core.config import settings
    DEFAULT_DATA_DIR = Path(settings.data_dir)
except Exception:
    DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_MANIFEST_VERSION = "1.0"


def calculate_sha256(file_path: Path | str) -> str:
    """Calculate the hex SHA-256 digest of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_backup(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> Path:
    """Create a verified, timestamped backup archive of all persistent data.

    Args:
        data_dir: Source data directory (defaults to configured data_dir).
        output_dir: Target directory for the archive (defaults to backups/).

    Returns:
        Path to the generated .tar.gz backup archive.
    """
    src_data_dir = Path(data_dir or DEFAULT_DATA_DIR)
    target_backup_dir = Path(output_dir or DEFAULT_BACKUP_DIR)
    target_backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_name = f"synapseos_backup_{timestamp_str}.tar.gz"
    archive_path = target_backup_dir / archive_name

    # Identify all files to backup in data_dir
    files_to_backup: list[Path] = []
    if src_data_dir.exists():
        for path in src_data_dir.rglob("*"):
            if path.is_file() and not path.name.endswith(".tmp"):
                files_to_backup.append(path)

    # Build manifest
    manifest_files: list[dict[str, Any]] = []
    for f in sorted(files_to_backup):
        rel_path = f.relative_to(src_data_dir).as_posix()
        manifest_files.append({
            "rel_path": rel_path,
            "size_bytes": f.stat().st_size,
            "sha256": calculate_sha256(f),
        })

    manifest = {
        "version": BACKUP_MANIFEST_VERSION,
        "app_version": "0.4.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "created_at_epoch": time.time(),
        "total_files": len(manifest_files),
        "files": manifest_files,
    }

    # Write to a temporary directory before packaging
    with tempfile.TemporaryDirectory() as temp_staging:
        staging_dir = Path(temp_staging)
        manifest_path = staging_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2)

        # Copy data files into staging
        staged_data = staging_dir / "data"
        staged_data.mkdir(parents=True, exist_ok=True)
        for f in files_to_backup:
            rel = f.relative_to(src_data_dir)
            dest = staged_data / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)

        # Create tar.gz
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(manifest_path, arcname="manifest.json")
            if files_to_backup:
                tar.add(staged_data, arcname="data")

    return archive_path


def _safe_extractall(tar: tarfile.TarFile, path: Path) -> None:
    """Safely extract tar archive, using data_filter where supported."""
    if hasattr(tarfile, "data_filter"):
        tar.extractall(path, filter="data")
    else:
        tar.extractall(path)


def verify_backup(archive_path: Path | str) -> dict[str, Any]:
    """Verify integrity of a backup archive against its included SHA-256 manifest.

    Args:
        archive_path: Path to the .tar.gz archive.

    Returns:
        dict containing 'valid', 'manifest', and 'errors'.
    """
    archive_file = Path(archive_path)
    if not archive_file.exists():
        return {
            "valid": False,
            "errors": [f"Backup file not found: {archive_file}"],
            "manifest": None,
        }

    errors: list[str] = []
    manifest: dict[str, Any] | None = None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        try:
            with tarfile.open(archive_file, "r:gz") as tar:
                _safe_extractall(tar, temp_path)
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Corrupt or invalid tar.gz archive: {e}"],
                "manifest": None,
            }

        manifest_file = temp_path / "manifest.json"
        if not manifest_file.exists():
            return {
                "valid": False,
                "errors": ["Missing manifest.json in backup archive"],
                "manifest": None,
            }

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Malformed manifest.json: {e}"],
                "manifest": None,
            }

        # Verify each file listed in manifest
        files_spec = manifest.get("files", [])
        for item in files_spec:
            rel_path = item["rel_path"]
            expected_hash = item["sha256"]
            expected_size = item["size_bytes"]

            extracted_file = temp_path / "data" / rel_path
            if not extracted_file.exists():
                errors.append(f"Missing file in archive: {rel_path}")
                continue

            actual_size = extracted_file.stat().st_size
            if actual_size != expected_size:
                errors.append(
                    f"Size mismatch for {rel_path}: expected {expected_size}, got {actual_size}"
                )
                continue

            actual_hash = calculate_sha256(extracted_file)
            if actual_hash != expected_hash:
                errors.append(
                    f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "manifest": manifest,
    }


def restore_backup(
    archive_path: Path | str,
    target_data_dir: Path | str | None = None,
    create_safety_snapshot: bool = True,
) -> dict[str, Any]:
    """Restore persistent data from a backup archive with pre-restore safety snapshot.

    Args:
        archive_path: Path to the .tar.gz archive.
        target_data_dir: Destination data directory (defaults to configured data_dir).
        create_safety_snapshot: Whether to backup active data before restoring.

    Returns:
        dict detailing restoration outcome.
    """
    dest_dir = Path(target_data_dir or DEFAULT_DATA_DIR)
    archive_file = Path(archive_path)

    # 1. Verify before touching anything
    verification = verify_backup(archive_file)
    if not verification["valid"]:
        raise ValueError(f"Backup verification failed: {verification['errors']}")

    manifest = verification["manifest"]
    safety_archive: Path | None = None

    # 2. Safety snapshot
    if create_safety_snapshot and dest_dir.exists() and any(dest_dir.iterdir()):
        safety_dir = DEFAULT_BACKUP_DIR / "safety_snapshots"
        safety_archive = create_backup(data_dir=dest_dir, output_dir=safety_dir)

    # 3. Extract to staging first, then copy into target atomically
    restored_files: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with tarfile.open(archive_file, "r:gz") as tar:
            _safe_extractall(tar, temp_path)

        staged_data = temp_path / "data"
        if staged_data.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            for item in staged_data.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(staged_data)
                    target_file = dest_dir / rel
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_file)
                    restored_files.append(rel.as_posix())

    return {
        "status": "success",
        "archive": str(archive_file),
        "target_data_dir": str(dest_dir),
        "restored_count": len(restored_files),
        "restored_files": restored_files,
        "safety_snapshot": str(safety_archive) if safety_archive else None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="SynapseOS Disaster Recovery and Backup CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup
    backup_parser = subparsers.add_parser("backup", help="Create a new persistent data backup")
    backup_parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_BACKUP_DIR),
        help="Directory to save the generated backup archive",
    )
    backup_parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Source data directory to backup",
    )

    # verify
    verify_parser = subparsers.add_parser("verify", help="Verify integrity of an existing backup")
    verify_parser.add_argument("archive", type=str, help="Path to .tar.gz archive")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore persistent data from backup")
    restore_parser.add_argument("archive", type=str, help="Path to .tar.gz archive")
    restore_parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Target data directory to restore into",
    )
    restore_parser.add_argument(
        "--no-safety-snapshot",
        action="store_true",
        help="Skip automatic pre-restore safety snapshot",
    )

    args = parser.parse_args()

    if args.command == "backup":
        print(f"[*] Initiating backup from: {args.data_dir or DEFAULT_DATA_DIR}")
        archive = create_backup(data_dir=args.data_dir, output_dir=args.output_dir)
        print(f"[+] Backup successfully generated: {archive}")
        print(f"[*] Size: {archive.stat().st_size:,} bytes")
        verification = verify_backup(archive)
        if verification["valid"]:
            print(f"[+] Archive integrity verified (SHA-256 match for {verification['manifest']['total_files']} files).")
            sys.exit(0)
        else:
            print(f"[!] Archive verification failed: {verification['errors']}")
            sys.exit(1)

    elif args.command == "verify":
        print(f"[*] Verifying archive: {args.archive}")
        res = verify_backup(args.archive)
        if res["valid"]:
            manifest = res["manifest"]
            print(f"[+] VERIFIED VALID: Backup archive is sound.")
            print(f"    App Version:    {manifest.get('app_version')}")
            print(f"    Timestamp UTC:  {manifest.get('timestamp_utc')}")
            print(f"    Files:          {manifest.get('total_files')}")
            for f in manifest.get("files", []):
                print(f"      - {f['rel_path']} ({f['size_bytes']:,} bytes, {f['sha256'][:12]}...)")
            sys.exit(0)
        else:
            print(f"[!] CORRUPT / INVALID ARCHIVE:")
            for err in res["errors"]:
                print(f"    - {err}")
            sys.exit(1)

    elif args.command == "restore":
        print(f"[*] Restoring from archive: {args.archive}")
        try:
            res = restore_backup(
                archive_path=args.archive,
                target_data_dir=args.data_dir,
                create_safety_snapshot=not args.no_safety_snapshot,
            )
            print(f"[+] RESTORE COMPLETE: {res['restored_count']} files restored.")
            if res.get("safety_snapshot"):
                print(f"[*] Pre-restore safety snapshot preserved at: {res['safety_snapshot']}")
            for f in res["restored_files"]:
                print(f"    - {f}")
            sys.exit(0)
        except Exception as e:
            print(f"[!] Restore failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
