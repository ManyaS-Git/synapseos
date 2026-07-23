#!/usr/bin/env bash
# =============================================================================
# SynapseOS — Teardown Script
# =============================================================================

set -euo pipefail

echo "🧹 Tearing down SynapseOS..."

# Stop all services
docker compose down

# Optionally remove volumes
read -p "Remove all data volumes? This will delete all data! (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down -v
    echo "✅ All volumes removed."
else
    echo "✅ Volumes preserved."
fi

echo "✅ Teardown complete."
