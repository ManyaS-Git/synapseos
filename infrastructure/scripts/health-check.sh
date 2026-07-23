#!/usr/bin/env bash
# =============================================================================
# SynapseOS — Health Check Script
# =============================================================================

set -euo pipefail

echo "🏥 SynapseOS Health Check"
echo "========================="

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "  ✅ $name: healthy"
    else
        echo "  ❌ $name: unhealthy"
    fi
}

check_service "API" "http://localhost:8000/health"
check_service "Web" "http://localhost:3000"
check_service "Neo4j" "http://localhost:7474"
check_service "Qdrant" "http://localhost:6333/healthz"
check_service "Redis" "http://localhost:6379"

echo ""
echo "Done."
