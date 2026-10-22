# Changelog

All notable changes to SynapseOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-21 (Nebius x NVIDIA Global AI Hackathon Release)

### Added
- **Nebius Token Factory & NVIDIA Nemotron Engine** (`app/core/llm/nebius.py`):
  - Server-side client integrating Nebius Token Factory API (`https://api.tokenfactory.nebius.com/v1/`).
  - Native integration with `nvidia/nemotron-4-340b-instruct` and `nvidia/llama-3.1-nemotron-70b-instruct`.
  - Pydantic structured output validation with automatic schema generation and JSON repair.
  - Model latency and token metrics tracking with strict prompt redaction (zero private prompt logging).
  - Deterministic simulated fallback for offline testing, local development, and CI environments without live cloud credentials.
- **Evidence-Backed RAG Pipeline** (`app/rag/pipeline.py`):
  - Semantic vector search grounded in workspace-isolated memories.
  - Authoritative verification against PostgreSQL active records.
  - Verifiable source citations linking memory ID, title, and excerpt.
  - Strict abstention guard refusing to hallucinate when evidence is absent or similarity is below threshold.
  - Dedicated RAG endpoint `POST /api/v1/rag/query`.
- **Bounded Agent Runtime & Human-in-the-Loop Safety** (`app/agents/runtime.py`, `app/agents/tools.py`):
  - Registered deterministic tools (`search_knowledge`, `create_memory`, `create_project`, `generate_plan`, `web_research`).
  - Explicit Pydantic validation for all tool arguments.
  - Consequential action gating requiring explicit user approval before execution.
  - Ephemeral approval session store with time-bounded tokens.
  - Dedicated endpoints `POST /api/v1/agent/chat`, `POST /api/v1/agent/approve`, and `GET /api/v1/agent/tools`.
- **Controlled Reflection & Memory Evolution** (`app/reflection/engine.py`):
  - Post-action outcome analysis and lesson extraction.
  - Automatic persistence of transparent `observation` memories.
  - Strict architectural boundary preventing autonomous modification of security rules, code, or permissions.
- **Frontend Assistant Copilot Interface** (`apps/web/src/app/assistant/page.tsx`):
  - Full conversational assistant powered by NVIDIA Nemotron.
  - Visual plan execution cards with status indicators.
  - Interactive approval/decline action banner for consequential operations.
  - Source citations side-drawer with similarity scores and excerpts.
  - Reflection summary cards displaying lessons learned from completed workflows.
- **Privacy & Model-Routing Settings** (`apps/web/src/app/settings/page.tsx`):
  - Interactive configuration for Hybrid Cloud, Local-First, and Cloud-Accelerated routing.
  - Nebius Token Factory live connection indicator.
  - Client-side redaction and zero prompt logging indicators.
- **Comprehensive Benchmark Suite** (`scripts/evaluate_rag_agent.py`):
  - Automated evaluation across retrieval recall, citation attribution, abstention rates, and approval gates.
  - Real metrics reporting with JSON export to `scripts/evaluation_results.json`.
- **Open Source Licensing**:
  - Apache License 2.0 applied for public hackathon distribution.

### Fixed
- Fixed Neo4j 5.x async driver import in `app/core/database.py` (`AsyncGraphDatabase`).
- Fixed Python module shadowing in `app/core/security/`.
- Fixed frontend package dependencies (`tailwindcss-animate` in `apps/web/package.json`).
- Fixed ESLint configuration for browser globals in monorepo root `.eslintrc.js`.

---

## [0.1.0] - 2026-10-01

### Added
- Initial project architecture and monorepo structure.
- Docker Compose configuration for PostgreSQL, Qdrant, Neo4j, and Redis.
- Initial Next.js 14 frontend skeleton and FastAPI backend skeleton.
- JWT authentication and workspace isolation models.
