<p align="center">
  <img src="docs/images/banner.svg" alt="SynapseOS — the privacy-first personal AI operating system that remembers, reasons, and acts" width="100%" />
</p>

<h1 align="center">SynapseOS</h1>

<p align="center">
  <strong>The privacy-first personal AI operating system that remembers, reasons, and acts — with you in control.</strong>
</p>

<p align="center">
  <a href="https://synapseos-three.vercel.app"><img src="https://img.shields.io/badge/LIVE_APP-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Live App" /></a>
  <a href="https://synapseos-three.vercel.app/showcase"><img src="https://img.shields.io/badge/60_SEC_PREVIEW-No_Signup-34D399?style=for-the-badge&logo=vercel&logoColor=white" alt="No-signup product preview" /></a>
  <a href="https://synapseos-api-2onj.onrender.com/docs"><img src="https://img.shields.io/badge/API_DOCS-Swagger-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="API Docs" /></a>
  <a href="https://synapseos-api-2onj.onrender.com/health"><img src="https://img.shields.io/badge/API_HEALTH-Operational-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Health" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Nebius_Token_Factory-00D47E?style=flat-square" alt="Nebius Token Factory" />
  <img src="https://img.shields.io/badge/NVIDIA_Nemotron-76B900?style=flat-square&logo=nvidia&logoColor=white" alt="NVIDIA Nemotron" />
  <img src="https://img.shields.io/badge/Next.js_14-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js 14" />
  <img src="https://img.shields.io/badge/FastAPI-Python_3.12-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Tests-102_passed_%7C_1_skipped-2ea44f?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/Live_probes-15%2F15-2ea44f?style=flat-square" alt="Live probes" />
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square" alt="License" />
</p>

<p align="center">
  <sub>Built for the <strong>Nebius × NVIDIA Global AI Hackathon 2026</strong> · API v0.4.0 · Deployed on Vercel + Render</sub>
</p>

---

## ⚡ Try it in 60 seconds

| | |
| :--- | :--- |
| **🚀 Live product** | [synapseos-three.vercel.app](https://synapseos-three.vercel.app) |
| **👀 No-signup preview** | [synapseos-three.vercel.app/showcase](https://synapseos-three.vercel.app/showcase) — seeded demo workspace, full UI |
| **📖 Interactive API** | [synapseos-api-2onj.onrender.com/docs](https://synapseos-api-2onj.onrender.com/docs) |
| **💚 Health probe** | [synapseos-api-2onj.onrender.com/health](https://synapseos-api-2onj.onrender.com/health) |

> [!NOTE]
> The backend runs on Render's free tier and sleeps after inactivity. The first request may take **30–45 seconds** while the container cold-starts.
>
> **Deployment transparency:** the public API currently runs in **deterministic simulation mode** because `NEBIUS_API_KEY` is not configured. The UI and API label every simulated generation; no claim of live inference is made. Adding a key to Render enables the live Nebius path without code changes. See [Deployment reality](#deployment-reality).

---

## 🧠 What is SynapseOS?

Cloud assistants forget everything the moment a session ends. Local note apps remember, but cannot reason. Agent frameworks can act, but usually do so inside an opaque trust boundary.

**SynapseOS closes that loop.** It is a full-stack personal AI operating system built around three guarantees:

| Pillar | What it means in practice |
| :--- | :--- |
| **Persistent, multi-modal memory** | Notes, documents, projects, and observations are stored relationally, as vectors, and as a knowledge graph — all scoped to a workspace. |
| **Evidence-backed reasoning** | Every RAG answer is grounded in retrieved chunks with citations. If the evidence is insufficient, the system abstains instead of inventing an answer. |
| **Bounded, human-approved action** | The agent plans in structured steps, auto-executes safe tools, and pauses consequential tools behind a durable, single-use approval gate. |

The result is an AI that can **remember your context, explain its reasoning, and take action safely** — not just generate plausible text.

---

## 📸 Product tour

> These are **full-page screenshots** of SynapseOS, captured from the `/showcase` experience and the public entry pages using a seeded sample workspace. They show the real product UI and contain no live user data. The public deployment runs in deterministic simulation mode; inference badges read **Simulation Mode** until `NEBIUS_API_KEY` is configured.

### Command center

<p align="center">
  <a href="docs/images/screenshot_overview.jpg"><img src="docs/images/screenshot_overview.jpg" alt="Full SynapseOS workspace overview with memory counts, grounded-recall telemetry, recent memories, and system status" width="100%" /></a>
</p>

<p align="center"><sub><strong>Workspace overview (complete page)</strong> — memory health, grounded-recall telemetry, recent memories, and live infrastructure status in one view.</sub></p>

### Assistant + human approval gate

<p align="center">
  <a href="docs/images/screenshot_assistant.jpg"><img src="docs/images/screenshot_assistant.jpg" alt="Full SynapseOS assistant page showing a three-step plan, a simulation-mode inference badge, and a human approval card for create_project" width="100%" /></a>
</p>

<p align="center"><sub><strong>Assistant copilot (complete page)</strong> — a three-step plan pauses at a single-use approval gate before the consequential <code>create_project</code> tool can run. The badge identifies simulated inference.</sub></p>

### Memory, graph, documents, and agents

<table>
<tr>
<td width="50%" valign="top">
  <a href="docs/images/screenshot_memory.jpg"><img src="docs/images/screenshot_memory.jpg" alt="Full SynapseOS memory manager page with persistent memory entries, provenance, and semantic search" width="100%" /></a>
  <p align="center"><sub><strong>Memory manager</strong> — durable memories, document extracts, provenance, and semantic search.</sub></p>
</td>
<td width="50%" valign="top">
  <a href="docs/images/screenshot_graph.jpg"><img src="docs/images/screenshot_graph.jpg" alt="Full SynapseOS knowledge graph page showing memory entities, relationships, and similarity controls" width="100%" /></a>
  <p align="center"><sub><strong>Knowledge graph</strong> — explore entities, memory clusters, and relationships with similarity thresholds.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
  <a href="docs/images/screenshot_documents.jpg"><img src="docs/images/screenshot_documents.jpg" alt="Full SynapseOS documents page with ingestion status, supported formats, and document inventory" width="100%" /></a>
  <p align="center"><sub><strong>Documents</strong> — ingestion, format support, processing status, and the workspace document inventory.</sub></p>
</td>
<td width="50%" valign="top">
  <a href="docs/images/screenshot_agents.jpg"><img src="docs/images/screenshot_agents.jpg" alt="Full SynapseOS agents page with the bounded agent runtime, tool registry, and execution guardrails" width="100%" /></a>
  <p align="center"><sub><strong>Agents</strong> — the bounded agent runtime, tool registry, and execution guardrails.</sub></p>
</td>
</tr>
</table>

### Activity, authentication, and landing page

<table>
<tr>
<td width="33.33%" valign="top">
  <a href="docs/images/screenshot_activity.jpg"><img src="docs/images/screenshot_activity.jpg" alt="Full SynapseOS activity page with audit events and runtime traces" width="100%" /></a>
  <p align="center"><sub><strong>Activity</strong> — audit events and runtime traces.</sub></p>
</td>
<td width="33.33%" valign="top">
  <a href="docs/images/screenshot_login.jpg"><img src="docs/images/screenshot_login.jpg" alt="Full SynapseOS login page" width="100%" /></a>
  <p align="center"><sub><strong>Login</strong> — local or Clerk-backed authentication.</sub></p>
</td>
<td width="33.33%" valign="top">
  <a href="docs/images/screenshot_register.jpg"><img src="docs/images/screenshot_register.jpg" alt="Full SynapseOS registration page" width="100%" /></a>
  <p align="center"><sub><strong>Registration</strong> — create a workspace and start with a private memory vault.</sub></p>
</td>
</tr>
</table>

<details>
<summary><strong>Landing page — open the complete full-page capture</strong></summary>
<p align="center">
  <a href="docs/images/screenshot_landing.jpg"><img src="docs/images/screenshot_landing.jpg" alt="Complete SynapseOS landing page including hero, product pillars, architecture, privacy posture, and call to action" width="38%" /></a>
</p>
<p align="center"><sub><strong>Landing page (complete page)</strong> — hero, product pillars, memory architecture, privacy posture, and call to action. Click the image for the full-resolution capture.</sub></p>
</details>

### Complete app pages

Full-page captures of every SynapseOS surface, taken from the seeded demo workspace on `/showcase` and the public entry pages. No live user data is shown.

| | | |
| :--- | :--- | :--- |
| **🏠 Landing** | [![Landing](docs/images/screenshots/screenshot_landing.png)](docs/images/screenshots/screenshot_landing.png) | Homepage hero, features, and call to action |
| **🔐 Login** | [![Login](docs/images/screenshots/screenshot_login.png)](docs/images/screenshots/screenshot_login.png) | Clerk-backed sign-in with development mode |
| **📝 Register** | [![Register](docs/images/screenshots/screenshot_register.png)](docs/images/screenshots/screenshot_register.png) | Account creation flow |
| **📊 Dashboard / Overview** | [![Overview](docs/images/screenshots/screenshot_overview.png)](docs/images/screenshots/screenshot_overview.png) | Memory counts, health, pending actions, knowledge activity |
| **💬 Assistant** | [![Assistant](docs/images/screenshots/screenshot_assistant.png)](docs/images/screenshots/screenshot_assistant.png) | Copilot with agent reasoning, grounded RAG, and approval gate |
| **🧠 Memory** | [![Memory](docs/images/screenshots/screenshot_memory.png)](docs/images/screenshots/screenshot_memory.png) | Persistent memory manager with semantic search |
| **🕸️ Knowledge Graph** | [![Graph](docs/images/screenshots/screenshot_graph.png)](docs/images/screenshots/screenshot_graph.png) | Memory entities, relationships, and similarity |
| **📄 Documents** | [![Documents](docs/images/screenshots/screenshot_documents.png)](docs/images/screenshots/screenshot_documents.png) | Ingestion status and document inventory |
| **🤖 Agents** | [![Agents](docs/images/screenshots/screenshot_agents.png)](docs/images/screenshots/screenshot_agents.png) | Bounded agent runtime and safety controls |
| **📈 Activity** | [![Activity](docs/images/screenshots/screenshot_activity.png)](docs/images/screenshots/screenshot_activity.png) | Audit trail and runtime traces |

### A 3-minute judge tour

1. **Open the [no-signup showcase](https://synapseos-three.vercel.app/showcase)** and scan the dashboard. Note the memory count, workspace selector, and grounded-recall metric.
2. **Ask the copilot a question** that requires stored context. Inspect the citation chips — the answer is tied to retrieved evidence, not free-floating generation.
3. **Trigger a consequential action** such as creating a project. The runtime pauses and renders an approval card with the action, arguments, and risk level.
4. **Approve or reject it.** Approval is single-use and tenant-scoped; rejection is terminal and the tool never runs.
5. **Open the knowledge graph** to see how the same memories are linked as entities and relationships.
6. **Hit `/health/ready`** and `/docs` to inspect the live API and its OpenAPI schema.
7. **Read the [benchmark results](#verification--benchmarks)** — every number below was produced by the harnesses in this repository.

> **A demo script that lands well**
>
> 1. Ask *“What is the launch date for Apollo phase 1?”* → semantic retrieval plus a grounded citation.
> 2. Ask *“What is the budget for the Mars colony?”* → explicit abstention instead of a fabricated answer.
> 3. Say *“Create a new project called Mars Base”* → the runtime halts at the approval gate.
> 4. Reject the action → nothing is written, and the rejection is recorded in the trace.

---

## 🏗️ Architecture

<p align="center">
  <img src="docs/images/architecture.svg" alt="SynapseOS four-layer architecture: clients, FastAPI gateway, intelligence core, inference, and persistence" width="100%" />
</p>

SynapseOS is a four-layer system:

1. **Experience layer** — Next.js 14 App Router, React 18, TypeScript, Tailwind, Zustand, TanStack Query, and React Flow.
2. **Gateway layer** — FastAPI with Clerk RS256 / local HS256 dual-mode auth, workspace isolation, request tracing, and rate limiting.
3. **Intelligence core** — RAG pipeline, bounded agent runtime, tool registry, approval store, reflection engine, and document ingestion.
4. **State + inference layer** — SQLite/PostgreSQL, local vector index/Qdrant, local graph/Neo4j, JSON/Redis approval sessions, and Nebius Token Factory with deterministic simulation fallback.

### Component view

```mermaid
flowchart TB
    subgraph Client["🖥️ Experience layer"]
        Web["Next.js 14 web app<br/>Dashboard · Copilot · Graph · Memory"]
        Controls["Privacy & model controls<br/>hybrid · local_only · cloud_only"]
    end

    subgraph Gateway["🛡️ FastAPI gateway"]
        Auth["Auth & workspace isolation<br/>Clerk RS256 · local HS256"]
        API["REST API v1<br/>20+ endpoints"]
        Obs["Request IDs · security headers<br/>telemetry without prompts"]
    end

    subgraph Core["🧠 Intelligence core"]
        RAG["RAG pipeline<br/>retrieval · citations · abstention"]
        Agent["Bounded agent runtime<br/>plan · execute · approve"]
        Tools["Tool registry<br/>search · memory · project · plan · research"]
        Approval["Durable approval store<br/>900s TTL · single use"]
        Reflection["Reflection engine<br/>outcome → observation"]
        Ingest["Document ingestion<br/>md · txt · json · csv · pdf"]
    end

    subgraph Inference["⚡ Inference"]
        Nebius["Nebius Token Factory<br/>NVIDIA Nemotron"]
        Sim["Deterministic simulation<br/>zero-key fallback"]
        Local["Local Ollama<br/>optional private mode"]
    end

    subgraph Storage["💾 Persistence"]
        SQL[("SQLite / PostgreSQL<br/>users · workspaces · memories")]
        Vec[("Local vectors / Qdrant<br/>dense embeddings")]
        Graph[("Local graph / Neo4j<br/>entities · relations")]
        Session[("JSON / Redis<br/>approval sessions")]
    end

    Web --> Auth
    Controls --> Auth
    Auth --> API
    API --> RAG
    API --> Agent
    API --> Ingest
    Agent --> Tools
    Agent --> Approval
    Agent --> Reflection
    RAG --> Nebius
    Agent --> Nebius
    Reflection --> Nebius
    Nebius -.-> Sim
    Nebius -.-> Local
    RAG --> Vec
    RAG --> Graph
    Agent --> SQL
    Ingest --> SQL
    Ingest --> Vec
    Ingest --> Graph
    Approval --> Session
```

### Request lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Next.js UI
    participant API as FastAPI
    participant Auth as Auth + workspace guard
    participant RAG as RAG pipeline
    participant LLM as Nebius / simulation
    participant DB as Memory + vector + graph

    User->>UI: Ask a question or request an action
    UI->>API: POST /api/v1/rag/query or /agent/chat
    API->>Auth: Verify Clerk RS256 / local HS256 + workspace
    Auth-->>API: Authorized principal
    API->>RAG: Retrieve within workspace boundary
    RAG->>DB: Vector + relational + graph search
    DB-->>RAG: Ranked evidence chunks
    RAG->>LLM: Grounded synthesis request
    LLM-->>RAG: Answer + citation mapping
    alt Evidence is sufficient
        RAG-->>API: Cited answer
    else Evidence is insufficient
        RAG-->>API: Explicit abstention
    end
    API-->>UI: Response with provenance + provider metadata
    UI-->>User: Answer, citations, and model attribution
```

---

## 🔁 The memory-to-action loop

SynapseOS is not a chatbot with a memory table bolted on. It runs a bounded loop from context to action and back to memory:

```mermaid
flowchart LR
    A["1 · Intent<br/>user goal"] --> B["2 · Recall<br/>workspace-scoped retrieval"]
    B --> C["3 · Plan<br/>structured, typed steps"]
    C --> D{"4 · Consequential?"}
    D -- "No" --> E["5a · Execute safe tool<br/>search · plan · research"]
    D -- "Yes" --> F["5b · Approval gate<br/>900s TTL · single use"]
    F -- "Approve" --> G["6 · Execute with guards<br/>SSRF · tenant checks"]
    F -- "Reject" --> H["Terminal cancellation<br/>tool never runs"]
    E --> I["7 · Reflect<br/>outcome → observation"]
    G --> I
    H --> I
    I --> J[("Persistent memory<br/>next loop starts smarter")]
```

### Step by step

1. **Intent** — The user asks a question or requests an outcome.
2. **Recall** — Retrieval is scoped to the authenticated user's workspace. Cross-workspace hits are rejected, not filtered after the fact.
3. **Plan** — The runtime produces a structured plan with typed arguments and predicted impact.
4. **Risk classification** — Tools are explicitly marked safe or consequential.
5. **Execution or approval** — Safe tools run automatically. Consequential tools create a durable approval session and pause.
6. **Guarded execution** — Approved actions run with tenant checks and SSRF protection. Rejections are terminal.
7. **Reflection** — The outcome is synthesized into an observational memory, so the next loop has better context.

### The five agent tools

| Tool | Type | Purpose |
| :--- | :--- | :--- |
| `search_knowledge` | Safe | Semantic + lexical retrieval across the workspace |
| `generate_plan` | Safe | Structured decomposition of a multi-step goal |
| `web_research` | Safe | External research through an SSRF-hardened fetcher |
| `create_memory` | Safe | Persist a new observation or note with provenance |
| `create_project` | **Consequential** | Create a durable project; requires explicit human approval |

> Approval sessions are stored durably (JSON locally, Redis in distributed mode), expire after **900 seconds**, and are atomically consumed exactly once. A user cannot approve another user's session.

---

## 🔍 RAG with citations and abstention

```mermaid
flowchart TB
    Q["User query"] --> G["Workspace boundary check"]
    G --> H["Hybrid retrieval<br/>vector + relational + graph"]
    H --> R["Re-rank and threshold"]
    R --> S{"Evidence above<br/>grounding threshold?"}
    S -- "No" --> X["Abstain explicitly<br/>no fabricated answer"]
    S -- "Yes" --> C["Build cited context<br/>chunk IDs + source metadata"]
    C --> P["Prompt-injection sanitization"]
    P --> L["Nemotron synthesis<br/>structured output + repair"]
    L --> V["Validate citations<br/>against retrieved chunks"]
    V --> A["Answer + provenance +<br/>provider attribution"]
```

**What makes it defensible:**

- **Citations are validated**, not merely requested in a prompt.
- **Abstention is a first-class outcome.** Unsupported questions produce an explicit “I don’t have enough evidence” response.
- **Prompt injection is treated as untrusted content.** Instructions embedded in retrieved documents are neutralized before synthesis.
- **Provider attribution is visible.** The UI distinguishes live Nebius inference, simulation mode, and fallback, and reports latency.
- **Privacy mode is enforced server-side.** `PRIVACY_MODE=local_only` blocks external egress regardless of client behavior.

---

## 🛡️ Security model

SynapseOS assumes the model can be wrong, the network can be hostile, and the user’s data is not yours to leak.

| Control | Implementation |
| :--- | :--- |
| **Identity** | Clerk RS256 verification with JWKS discovery or PEM key; local HS256 dev mode; issuer and expiry validation |
| **Passwords** | Argon2id (`m=65536, t=3, p=4`) |
| **Sessions** | HTTP-only `SameSite=None; Secure` cookies plus Bearer fallback via `X-Access-Token` for cross-site deployments |
| **Tenant isolation** | Every CRUD, search, graph, RAG, and agent operation is authorized against the active workspace |
| **Authorization audit** | 17-point cross-user matrix covering memory, uploads, search, graphs, RAG, agent actions, approvals, and deletion |
| **Consequential actions** | Durable approval sessions, 900s TTL, atomic single-use consumption, tenant-scoped approval |
| **SSRF defense** | Blocks loopback, RFC 1918 private ranges, link-local, and cloud metadata (`169.254.169.254`) |
| **Prompt injection** | Retrieved content is sanitized and treated as data, never as instructions |
| **Secret handling** | API keys redacted from errors; server secrets never exposed through `NEXT_PUBLIC_*` |
| **Production invariants** | Rejects debug mode, weak/default secrets, wildcard CORS, and unsafe settings at startup |
| **Headers & tracing** | `nosniff`, `DENY`, XSS protection, strict referrer policy, and `X-Request-ID` correlation |
| **Upload safety** | Path-traversal-safe filenames, format validation, size limits, and explicit PDF text-extraction errors |
| **Backup integrity** | SHA-256 manifest, tamper detection, and pre-restore safety snapshots |

Security regression coverage includes **19 security audit tests** and **17 multi-tenant authorization tests**, plus dedicated Nebius, approval-store, RAG, upload, and backup suites.

---

<a id="verification--benchmarks" name="verification--benchmarks"></a>

## 📊 Verification & benchmarks

All numbers below were produced from the current repository state on **2026-10-30**.

### Test and deployment matrix

| Check | Result | Notes |
| :--- | :---: | :--- |
| Backend test suite | **102 passed · 1 skipped** | 33.26s; skip requires a live Nebius key |
| Live deployment probes | **15 / 15 passed** | Public Vercel + Render endpoints over HTTPS |
| Full-stack contract assertions | **12 / 12 passed** | Frontend/backend integration contracts |
| Security audit | **19 / 19 passed** | Settings invariants, headers, traversal, replay, SSRF |
| Multi-tenant authorization | **17 / 17 passed** | Two users, two workspaces, full endpoint matrix |
| RAG + agent benchmark | **52 queries evaluated** | Deterministic, seeded evaluation harness |
| API health | **`{"status":"healthy"}`** | Render free tier, cold-start aware |
| Inference verification | **`SIMULATION_VERIFIED`** | Live Nebius path is blocked until a key is configured |

### RAG + agent benchmark

Run with `python scripts/evaluate_rag_agent.py`.

| Metric | Result | Sample |
| :--- | :---: | :---: |
| Retrieval recall | **100%** | 41 / 41 |
| Citation grounding | **100%** | 32 / 32 |
| Abstention on unsupported queries | **93.3%** | 14 / 15 |
| Prompt-injection defense | **100%** | 3 / 3 |
| Cross-workspace isolation | **100%** | 3 / 3 |
| Safe tool autonomous execution | **100%** | 1 / 1 |
| Consequential approval gate | **100%** | 1 / 1 |
| Rejection guard | **100%** | 1 / 1 |
| Reflection generation | **100%** | 1 / 1 |

**How to read this honestly:**

- These are **deterministic, seeded evaluations** against a known corpus. They demonstrate behavior and regressions, not open-domain model quality.
- The one missed abstention is reported rather than rounded up. The system is designed to prefer abstaining over fabricating an answer.
- The public deployment is in simulation mode. The harness proves the orchestration, retrieval, safety, and citation logic; a configured `NEBIUS_API_KEY` swaps in live Nemotron generation.

---

## 🧩 Feature deep dive

### 1. Persistent multi-modal memory

- Relational records for users, workspaces, projects, memories, and audit events.
- Dense vector index for semantic similarity, with disk persistence in local mode and Qdrant support in distributed mode.
- Knowledge graph of entities and relationships, persisted locally or backed by Neo4j.
- Memory lifecycle: create, list, search, inspect, important-only, recent, per-project, graph, similarity, delete.
- Workspace isolation is enforced at the query layer — not in the UI.

### 2. Document ingestion

| Format | Support | Notes |
| :--- | :---: | :--- |
| Markdown (`.md`, `.markdown`) | ✅ | Structured text + metadata |
| Plain text (`.txt`, `.log`, `.rst`) | ✅ | UTF-8 / Latin-1, 10 MB limit |
| JSON (`.json`) | ✅ | Validation and formatted extraction |
| CSV (`.csv`) | ✅ | Row/column aware |
| PDF with text (`.pdf`) | ✅ | `pypdf`, 100-page limit, page markers |
| Scanned / image-only PDF | ❌ | Explicit HTTP 400: OCR is not supported |

Uploads are chunked, embedded, stored, and immediately available to retrieval and the graph.

### 3. Bounded agent runtime

- Structured planning with typed tool arguments.
- Explicit safe/consequential classification.
- Human approval before irreversible actions.
- Durable sessions that survive process restarts.
- Replay protection: a consumed approval can never be reused.
- Reflection that records outcomes without escalating privileges.

### 4. Reflection engine

After a task completes, the reflection engine synthesizes what happened into an observational memory. This closes the loop: future retrieval can use the outcome of past actions, while the agent's permissions remain unchanged.

### 5. Privacy controls

`PRIVACY_MODE` supports:

- **`hybrid`** — use Nebius when configured, fall back safely otherwise.
- **`local_only`** — block all external model egress.
- **`cloud_only`** — require the remote provider path.

Telemetry records latency, tokens, retries, and correlation IDs **without storing prompts**.

---

## 🧰 Tech stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14 App Router · React 18 · TypeScript · Tailwind CSS · Zustand · TanStack Query · React Flow · Lucide |
| **Backend** | FastAPI · Python 3.12 · Pydantic v2 · SQLAlchemy 2 async · Uvicorn · HTTPX · pypdf · structlog |
| **Auth** | Clerk (`@clerk/nextjs` v5) · RS256/JWKS · local HS256 · Argon2id |
| **Inference** | Nebius Token Factory · NVIDIA Nemotron (`nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` default) · deterministic simulation · optional Ollama |
| **Data** | SQLite/aiosqlite · PostgreSQL 16 · local JSON vectors · Qdrant · local JSON graph · Neo4j 5 · Redis 7 |
| **Deployment** | Vercel (frontend) · Render (API) · Docker Compose (standalone + distributed) · GitHub Actions |
| **Quality** | pytest · pytest-asyncio · Ruff · Black · mypy · ESLint · Prettier · TypeScript strict checks |

---

## 🚀 Quick start

### Prerequisites

- Node.js **20+** and npm 10+
- Python **3.12+**
- Docker + Docker Compose (optional, for containerized modes)

### Option A — Local development (fastest)

```bash
git clone https://github.com/ManyaS-Git/synapseos.git
cd synapseos
```

**Backend**

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

pip install -r apps/api/requirements.txt
cp .env.example .env
```

Edit `.env`, then start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir apps/api
```

**Frontend** (new terminal)

```bash
npm install
npm run dev -w @synapseos/web
```

Open:

- Web app: [http://localhost:3000](http://localhost:3000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

> With no `NEBIUS_API_KEY`, the backend runs in deterministic simulation mode so the full product remains explorable offline.

### Option B — Docker, standalone persistent mode

One API container plus one web container, with all state in a durable volume. No external databases required.

```bash
cp .env.example .env.production
# Set APP_ENV=production, APP_DEBUG=false, and strong secrets
docker compose -f docker-compose.prod.yml --env-file .env.production --profile standalone up -d --build
docker compose -f docker-compose.prod.yml ps
```

### Option C — Docker, distributed mode

PostgreSQL 16, Qdrant, Neo4j 5, Redis 7, the API, and the web app:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production --profile distributed up -d --build
```

The backend automatically selects embedded storage in development and strict distributed storage when `STORAGE_MODE=distributed`.

---

## 🔑 Configuration

| Variable | Scope | Required | Purpose |
| :--- | :--- | :---: | :--- |
| `APP_ENV` | Backend | ✅ | `development`, `staging`, `production`, `testing` |
| `APP_DEBUG` | Backend | ✅ | Must be `false` in production |
| `APP_SECRET_KEY` | Backend | ✅ | ≥ 16 chars; generated with `openssl rand -hex 32` |
| `JWT_SECRET_KEY` | Backend | ✅ | Local token signing secret |
| `STORAGE_MODE` | Backend | — | `local_embedded`, `auto`, or `distributed` |
| `NEBIUS_API_KEY` | Backend | Optional | Enables live Nebius inference; empty means simulation |
| `NEBIUS_BASE_URL` | Backend | — | Default `https://api.tokenfactory.nebius.com/v1` |
| `NEBIUS_MODEL` | Backend | — | Default `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` |
| `PRIVACY_MODE` | Backend | — | `hybrid`, `local_only`, or `cloud_only` |
| `NEXT_PUBLIC_API_URL` | Frontend | ✅ | Public backend base URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Frontend | ✅ for Clerk | Clerk publishable key |
| `CLERK_SECRET_KEY` | Backend / Edge | ✅ for Clerk | Clerk secret key |
| `CLERK_JWT_KEY` / `CLERK_JWKS_URL` | Backend | Optional | Networkless or cached RS256 verification |

> [!CAUTION]
> Never put backend secrets in `NEXT_PUBLIC_*` variables. They are embedded in the browser bundle.

Full variable reference: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) · Auth setup: [docs/CLERK_AUTH_SETUP.md](docs/CLERK_AUTH_SETUP.md) · Privacy: [docs/PRIVACY.md](docs/PRIVACY.md)

---

<a id="deployment-reality" name="deployment-reality"></a>

## ☁️ Deployment reality

### Live topology

| Component | Platform | URL | Observed status |
| :--- | :--- | :--- | :---: |
| Frontend | Vercel (Hobby) | [synapseos-three.vercel.app](https://synapseos-three.vercel.app) | ✅ HTTP 200 |
| API | Render (Free Web Service) | [synapseos-api-2onj.onrender.com](https://synapseos-api-2onj.onrender.com) | ✅ HTTP 200 |
| Swagger | Render | [/docs](https://synapseos-api-2onj.onrender.com/docs) | ✅ Active |
| Health | Render | [/health](https://synapseos-api-2onj.onrender.com/health) | ✅ `healthy` |
| Readiness | Render | [/health/ready](https://synapseos-api-2onj.onrender.com/health/ready) | ✅ `ready` (SQLite engine) |
| OpenAPI | Render | [/openapi.json](https://synapseos-api-2onj.onrender.com/openapi.json) | ✅ API v0.4.0 |

### What is real, and what is constrained

| Area | Status |
| :--- | :--- |
| Product UI, auth flows, memory CRUD, uploads, RAG, graph, agent planning, approval gate | **Live and verified** |
| Backend test suite, contract tests, security suite, benchmark harness | **Passing** |
| Live Nebius inference on the public deployment | **Simulation mode** — key not configured |
| Durable storage on Render free tier | **Ephemeral** — SQLite/JSON state resets on cold reboot or redeploy |
| Qdrant / Neo4j distributed path | **Implemented, not fully verified end-to-end** |
| Scanned-PDF OCR | **Not implemented** — explicit error, by design |

**To enable live inference on Render:**

1. Create a key at [tokenfactory.nebius.com](https://tokenfactory.nebius.com/).
2. In the Render service, set `NEBIUS_API_KEY` and confirm `NEBIUS_MODEL`.
3. Redeploy, then run:
   ```bash
   python scripts/verify_nebius_inference.py --remote-url https://synapseos-api-2onj.onrender.com
   ```
   A configured deployment reports `LIVE_PROVIDER_VERIFIED` instead of `SIMULATION_VERIFIED`.

**For durable production storage:** deploy with the `standalone` Compose profile on a VM with a persistent volume, or use the `distributed` profile with managed PostgreSQL, Qdrant, Neo4j, and Redis.

Deployment details: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) · Runbook: [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md)

---

## 📡 API reference

Base URL: `https://synapseos-api-2onj.onrender.com` · interactive schema at `/docs`.

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/` | `GET` | Service identity and version |
| `/health` | `GET` | Liveness, database, and LLM readiness |
| `/health/live` | `GET` | Process liveness |
| `/health/ready` | `GET` | Storage-engine readiness |
| `/api/v1/auth/register` | `POST` | Register with Argon2id hashing |
| `/api/v1/auth/login` | `POST` | Login; sets cookie and exposes `X-Access-Token` |
| `/api/v1/auth/logout` | `POST` | Clear session |
| `/api/v1/users/me` | `GET` | Current identity |
| `/api/v1/workspaces` | `GET` / `POST` | List or create workspaces |
| `/api/v1/projects` | `GET` / `POST` | List or create projects |
| `/api/v1/memory` | `GET` / `POST` | List or create memories |
| `/api/v1/memory/upload` | `POST` | Ingest md/txt/json/csv/pdf with chunking |
| `/api/v1/memory/search` | `GET` | Semantic memory search |
| `/api/v1/memory/recent` | `GET` | Recently created memories |
| `/api/v1/memory/important` | `GET` | High-importance memories |
| `/api/v1/memory/project/{project_id}` | `GET` | Project-scoped memories |
| `/api/v1/memory/graph` | `GET` | Knowledge graph nodes and edges |
| `/api/v1/memory/similarity` | `GET` | Similarity inspection |
| `/api/v1/memory/{memory_id}` | `DELETE` | Delete a memory across stores |
| `/api/v1/rag/query` | `POST` | Cited, abstention-aware RAG |
| `/api/v1/agent/chat` | `POST` | Plan and execute with approval gates |
| `/api/v1/agent/approve` | `POST` | Approve or reject a consequential action |
| `/api/v1/agent/tools` | `GET` | Inspect the tool registry |

---

## 🗂️ Project structure

```text
synapseos/
├── apps/
│   ├── api/                     # FastAPI backend
│   │   ├── app/
│   │   │   ├── agents/          # runtime, tools, approval store
│   │   │   ├── core/            # config, DB, security, LLM, telemetry
│   │   │   ├── rag/             # retrieval, citations, abstention
│   │   │   ├── reflection/      # outcome → observation engine
│   │   │   ├── routers/v1/      # REST endpoints
│   │   │   ├── services/memory/ # memory, vectors, graph, embedding
│   │   │   └── main.py          # app factory + middleware
│   │   └── tests/               # 102 backend tests
│   └── web/                     # Next.js 14 frontend
│       └── src/
│           ├── app/             # dashboard, assistant, graph, showcase
│           ├── components/      # UI system and product surfaces
│           ├── hooks/           # auth, data, product hooks
│           └── lib/             # API client, utils, contracts
├── docs/                        # architecture, deployment, audits, images
│   └── images/                  # banner, architecture SVG, screenshots
├── scripts/                     # benchmarks, live probes, backup/restore
├── tests/integration/           # durability + full-stack contracts
├── docker-compose.prod.yml      # standalone + distributed profiles
├── render.yaml                  # Render blueprint
└── .github/workflows/ci.yml     # CI pipeline
```

> `frontend/` at the repository root is the original v0 design reference. The canonical, deployed application is **`apps/web`**.

---

## 🧪 Testing

```bash
# Full backend suite (102 passed, 1 skipped)
python -m pytest apps/api/tests/ -v

# Security invariants (19 tests)
python -m pytest apps/api/tests/test_security_audit.py -v

# Multi-tenant authorization matrix (17 checks)
python -m pytest apps/api/tests/test_multi_tenant_authorization.py -v

# Full-stack frontend/backend contracts (12 assertions)
python -m pytest tests/integration/test_frontend_fullstack_contracts.py -v

# RAG + agent benchmark (52 queries)
python scripts/evaluate_rag_agent.py

# Live deployment probes (15 checks)
python scripts/verify_live_deployments.py

# Inference verification (simulation allowed)
python scripts/verify_nebius_inference.py --remote-url https://synapseos-api-2onj.onrender.com --allow-simulated

# Frontend production build
npm run build -w @synapseos/web
```

> On Windows hosts with Application Control, invoke pytest as `python -m pytest` rather than the `pytest.exe` shim.

More detail: [docs/TESTING.md](docs/TESTING.md)

---

## 📚 Documentation

| Document | Contents |
| :--- | :--- |
| [Architecture](docs/ARCHITECTURE.md) | Layer-by-layer system design |
| [Feature status](docs/FEATURE_STATUS.md) | Verified / simulated / blocked capability matrix |
| [Deployment](docs/DEPLOYMENT.md) | All four deployment tiers and env vars |
| [Operations runbook](docs/OPERATIONS_RUNBOOK.md) | Health checks, rollback, incident response |
| [Security & privacy](docs/PRIVACY.md) | Privacy modes, telemetry, data lifecycle |
| [Clerk auth setup](docs/CLERK_AUTH_SETUP.md) | Clerk + local auth configuration |
| [Final audit](docs/PHASE_6_FINAL_AUDIT.md) | Live deployment, security, and benchmark audit |
| [Demo guide](docs/DEMO_GUIDE.md) | Suggested walkthrough and talking points |
| [Testing](docs/TESTING.md) | Suites, fixtures, and commands |

---

## ⚠️ Honest limitations

SynapseOS is a production-shaped hackathon project, not a finished commercial product. The following constraints are real:

1. **Public inference is simulated.** The Render deployment has no `NEBIUS_API_KEY`. Generation is deterministic and clearly labeled. Live Nebius inference is implemented and unit-tested but not currently running in production.
2. **Render free-tier storage is ephemeral.** SQLite, local vectors, graph JSON, and approval sessions reset on cold reboot or redeploy. Durable deployments require a persistent volume or managed databases.
3. **Distributed backends are not fully verified end-to-end.** Qdrant and Neo4j code paths exist and are configurable, but the verified public path uses embedded storage.
4. **No OCR.** Scanned/image-only PDFs return a clear error instead of silently producing empty text.
5. **Benchmarks are seeded, not open-domain.** They measure retrieval, citation, abstention, isolation, and approval behavior against a controlled corpus.
6. **Rate limiting is in-memory by default.** Redis-backed limiting exists but is not fully verified under multi-worker load.
7. **Upstream npm advisories exist.** `next@14` and `postcss` have known advisories; remediation requires a breaking framework upgrade. The deployed Vercel surface does not expose the affected self-hosted server paths.
8. **No payment or billing flow.** The product is free to explore and designed for zero-cost operation.

These limitations are documented rather than hidden because trustworthy AI infrastructure requires trustworthy claims.

---

## 🏆 Hackathon alignment

| Criterion | How SynapseOS addresses it |
| :--- | :--- |
| **Nebius × NVIDIA integration** | Nebius Token Factory client for NVIDIA Nemotron with retries, structured JSON repair, telemetry, and a deterministic fallback |
| **Agentic behavior** | Multi-step planning, five typed tools, risk classification, durable approvals, rejection handling, and reflection |
| **Technical depth** | Hybrid retrieval, validated citations, abstention, workspace isolation, SSRF defense, prompt-injection handling, backup/restore |
| **Product completeness** | Auth, dashboard, copilot, memory manager, knowledge graph, uploads, settings, public showcase, and API docs |
| **Real deployment** | Live Vercel frontend and Render API, 15/15 probes passing, CI, Docker profiles, and an operations runbook |
| **Transparency** | Simulation and storage limitations are labeled in the UI, API, README, and audit docs |
| **Test discipline** | 102 backend tests, 12 contract assertions, 19 security tests, 17 authorization checks, and a 52-query benchmark |

---

## 🤝 Contributing

Contributions are welcome. Before opening a PR:

1. Run the backend suite and the frontend build.
2. Keep workspace isolation and approval semantics intact.
3. Add a regression test for every security-sensitive change.
4. Update `docs/FEATURE_STATUS.md` when capability status changes.

---

## 📄 License

Licensed under the [Apache License 2.0](LICENSE).

---

<p align="center">
  <strong>SynapseOS</strong> — memory with provenance, reasoning with evidence, action with consent.
</p>

<p align="center">
  Built with ❤️ by <a href="https://github.com/ManyaS-Git">ManyaS-Git</a> for the <strong>Nebius × NVIDIA Global AI Hackathon 2026</strong>.
</p>
