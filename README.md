<p align="center">
  <h1 align="center">SynapseOS</h1>
  <p align="center">
    <strong>Privacy-First AI Operating System</strong>
  </p>
  <p align="center">
    <em>This project is currently in active development. API and architecture are subject to change.</em>
  </p>
</p>

---

## Overview

SynapseOS is a privacy-first AI operating system that combines long-term memory, knowledge graphs, vector search, multi-agent AI, retrieval-augmented generation, and local/cloud LLM routing into a unified, self-evolving platform.

All data is stored locally by default. Nothing leaves your machine unless you explicitly configure external providers.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, React Flow, Zustand, TanStack Query |
| Backend | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy, Alembic |
| Databases | PostgreSQL, Qdrant (vectors), Neo4j (graphs), Redis (cache) |
| AI/ML | Ollama (local), LiteLLM (cloud routing), embeddings pipeline |
| Infrastructure | Docker Compose, GitHub Actions CI |
| Desktop | Electron (planned) |

## Architecture

```mermaid
graph TB
    subgraph "Frontend"
        Web[Next.js Web App]
        Desktop[Desktop App - Electron]
        SDK[JS/TS SDK]
    end

    subgraph "API Layer"
        FastAPI[FastAPI Backend]
        Router[LLM Router]
    end

    subgraph "Core Services"
        MemEngine[Memory Engine]
        KG[Knowledge Graph]
        RAG[RAG Pipeline]
        Embed[Embeddings]
        Reflect[Reflection Engine]
        Sched[Scheduler]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL)]
        Qdrant[(Qdrant)]
        Neo4j[(Neo4j)]
        Redis[(Redis)]
    end

    subgraph "LLM Providers"
        Ollama[Ollama - Local]
        LiteLLM[LiteLLM - Cloud]
    end

    Web --> FastAPI
    Desktop --> FastAPI
    SDK --> FastAPI
    FastAPI --> Router
    FastAPI --> MemEngine
    FastAPI --> KG
    FastAPI --> RAG
    RAG --> Embed
    Embed --> Qdrant
    MemEngine --> PG
    KG --> Neo4j
    FastAPI --> Redis
    Router --> Ollama
    Router --> LiteLLM
```

## Project Structure

```
synapseos/
├── apps/
│   ├── web/                  # Next.js frontend
│   ├── api/                  # FastAPI backend
│   └── desktop/              # Electron desktop app
├── packages/
│   ├── ui/                   # Shared UI components
│   ├── config/               # Shared configs (ESLint, Prettier, TS)
│   ├── types/                # Shared type definitions
│   ├── sdk/                  # JavaScript/TypeScript SDK
│   └── shared/               # Shared utilities
├── services/
│   ├── memory-engine/        # Long-term memory management
│   ├── agent-runtime/        # Multi-agent orchestration
│   ├── rag/                  # RAG pipeline
│   ├── reflection/           # Self-reflection & optimization
│   ├── embeddings/           # Embedding generation
│   ├── llm-router/           # Local/cloud LLM routing
│   ├── connectors/           # External data connectors
│   └── scheduler/            # Background task scheduling
├── infrastructure/
│   ├── docker/               # Docker configurations
│   ├── nginx/                # Reverse proxy
│   ├── monitoring/           # Prometheus, Grafana
│   └── scripts/              # Utility scripts
├── docs/                     # Internal documentation
└── tests/                    # Unit, integration, e2e tests
```

## Development Status

> **Status: In Active Development**

This project is confidential and not open for external contribution. The codebase is under active development — expect breaking changes.

| Component | Status |
|-----------|--------|
| Project Architecture | ✅ Complete |
| Docker Infrastructure | ✅ Complete |
| Backend API | 🔄 In Progress |
| Frontend UI | 🔄 In Progress |
| Memory Engine | ⏳ Planned |
| Agent System | ⏳ Planned |
| RAG Pipeline | ⏳ Planned |
| Knowledge Graph | ⏳ Planned |
| Desktop App | ⏳ Planned |
| SDK | ⏳ Planned |

## Getting Started (Development)

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### Docker (Recommended)

```bash
git clone https://github.com/ManyaS-Git/synapseos.git
cd synapseos
cp .env.example .env
docker compose up -d
```

**Service URLs:**
| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Neo4j | http://localhost:7474 |
| Qdrant | http://localhost:6333 |
| Grafana | http://localhost:3001 |

### Local Development

```bash
# Frontend
cd apps/web
npm install
npm run dev

# Backend
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Make Commands

```bash
make help          # List all available commands
make install       # Install all dependencies
make dev           # Start development servers
make lint          # Run linting
make test          # Run tests
make docker-up     # Start Docker services
make docker-down   # Stop Docker services
```

## Configuration

Environment variables are managed through `.env` files:

- `.env.example` — Template with all available variables
- `.env.development` — Local development defaults
- `.env.production` — Production overrides

Key configurations:

```env
# Core
APP_NAME=SynapseOS
APP_ENV=development
SECRET_KEY=your-secret-key

# Databases
DATABASE_URL=postgresql+asyncpg://synapseos:synapseos@localhost:5432/synapseos
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
QDRANT_URL=http://localhost:6333

# AI
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_PROVIDER=ollama
```

## Security

This is a private, confidential project. Do not distribute, fork, or share this codebase without explicit authorization.

See [SECURITY.md](SECURITY.md) for vulnerability reporting guidelines.

---

<p align="center">
  <em>SynapseOS — Privacy-first AI operating system</em>
</p>
