#!/usr/bin/env bash
# =============================================================================
# SynapseOS — Development Setup Script
# =============================================================================

set -euo pipefail

echo "🧠 Setting up SynapseOS development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Error: docker is required but not installed." >&2; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Error: docker compose is required but not installed." >&2; exit 1; }

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please review and update the values."
fi

# Start services
echo "🐳 Starting Docker services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Pull Ollama models
echo "🤖 Pulling default Ollama model..."
docker compose exec ollama ollama pull llama3.2 || echo "⚠️  Failed to pull Ollama model. You can do this manually later."

echo ""
echo "✅ SynapseOS development environment is ready!"
echo ""
echo "Services:"
echo "  Web UI:        http://localhost:3000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Neo4j:         http://localhost:7474"
echo "  Qdrant:        http://localhost:6333"
echo "  Prometheus:    http://localhost:9090 (with monitoring profile)"
echo "  Grafana:       http://localhost:3001 (with monitoring profile)"
echo ""
echo "To start with monitoring: docker compose --profile monitoring up -d"
