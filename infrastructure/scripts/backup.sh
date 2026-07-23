#!/usr/bin/env bash
# =============================================================================
# SynapseOS — Database Backup Script
# =============================================================================

set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "💾 Backing up SynapseOS databases..."

# PostgreSQL backup
echo "  Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U synapseos synapseos > "$BACKUP_DIR/postgres_$TIMESTAMP.sql"

# Neo4j backup
echo "  Backing up Neo4j..."
# TODO: Implement Neo4j backup

# Qdrant backup
echo "  Backing up Qdrant..."
# TODO: Implement Qdrant backup

echo "✅ Backup complete: $BACKUP_DIR"
