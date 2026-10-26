# SynapseOS — Hackathon Presentation & Judge Walkthrough Guide

This comprehensive guide is designed for hackathon evaluators, reviewers, and judges exploring the live deployment of **SynapseOS**.

---

## 1. Problem Statement & Technical Differentiators

Most AI assistants operate as stateless prompt wrappers. They forget context between sessions, hallucinate when information is missing, execute actions without safety boundaries, and route sensitive corporate or personal data to cloud providers without transparent egress controls.

**SynapseOS is a memory-first personal AI operating system** that solves these foundational challenges:

| Challenge in Standard AI | SynapseOS Technical Differentiator | Verification Evidence |
| :--- | :--- | :--- |
| **Statelessness** | **Persistent Hybrid Memory**: Combines SQLite relational persistence, vector embeddings, and an interactive knowledge graph. | `tests/integration/test_memory_durability.py` |
| **Hallucinations** | **Evidence-Backed RAG with Citations**: Answers are strictly grounded in workspace memory chunks with verifiable citations. | 100% citation grounding in 52-case benchmark |
| **Silent Fabrications** | **Principled Abstention**: When evidence is missing or insufficient, the system explicitly abstains rather than inventing answers. | 93.3% abstention rate on unsupported facts |
| **Unbounded Agent Risk** | **Human-in-the-Loop Consequential Barriers**: The agent runtime distinguishes safe actions from consequential actions (`create_project`, deletions) and halts execution until a human explicitly approves or rejects the step. | 100% rejection & replay protection in security audit |
| **Privacy Vulnerabilities** | **Hybrid Privacy Boundaries**: `PRIVACY_MODE=local_only` guarantees 0 bytes of external egress. Hybrid mode transmits only sanitized workspace excerpts over TLS 1.3 to Nebius Token Factory, never full documents, keys, or passwords. | Verified in `test_security_audit.py` |
| **Deceptive AI Attribution** | **100% Attribution Transparency**: Every assistant generation displays an honest badge distinguishing `Live Nebius AI` from `Simulation Mode`. | Dynamic UI attribution badges in `apps/web` |

---

## 2. Public Live Deployment Endpoints

| Component | Host / Tier | Public HTTPS URL | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | **Vercel** (Hobby Plan) | [https://synapseos-three.vercel.app](https://synapseos-three.vercel.app) | **PASS** (115 KB Next.js 14 bundle) |
| **Backend API** | **Render** (Free Web Service) | [https://synapseos-api-2onj.onrender.com](https://synapseos-api-2onj.onrender.com) | **PASS** (Service ID: `srv-dbdm9tg473hc73cs3rf0`) |
| **API Docs (Swagger)** | Render | [https://synapseos-api-2onj.onrender.com/docs](https://synapseos-api-2onj.onrender.com/docs) | **PASS** (Interactive OpenAPI UI) |
| **Health Probe** | Render | [https://synapseos-api-2onj.onrender.com/health](https://synapseos-api-2onj.onrender.com/health) | **PASS** (Status: `healthy`, 200 OK) |

> [!NOTE]
> **Free-Tier Cold Start Notice**:
> Render's free tier spins down after 15 minutes of inactivity. The first request after sleep experiences a **30 to 45 second wake-up delay**.
> The web interface features a live **API Status Indicator** (`API Connected` / `Waking API...`) in the top navigation bar and an automated recovery banner to ensure smooth evaluation.

---

## 3. Timed Presentation Tracks

### Track A: 3-Minute Fast Pitch & Core Demo
- **0:00 - 0:45**: Open [https://synapseos-three.vercel.app](https://synapseos-three.vercel.app). Explain the memory-first problem statement: personal AI must remember, reason with citations, and stop before taking irreversible actions.
- **0:45 - 1:45**: Navigate to **Memory**, show the knowledge graph and semantic search (`when is phase 1 starting?`). Switch to **Assistant**, ask about Apollo phase 1, and show the grounded citation pill.
- **1:45 - 2:30**: Ask a question outside the workspace context. Demonstrate **Principled Abstention** (zero hallucination).
- **2:30 - 3:00**: Issue a consequential command (`create a new project called Mars Base`). Show the execution halt at the **Human Approval Gate**, reject it, and demonstrate that zero unauthorized changes occurred.

---

### Track B: 5-Minute Interactive Judge Walkthrough (Single Coherent Scenario: "Project Apollo")

#### Step 1: Launch & Authenticate (45s)
1. Open [https://synapseos-three.vercel.app](https://synapseos-three.vercel.app) and click **Launch OS** or **Sign in**.
2. Sign in via Clerk (Google OAuth, email verification, or passwordless auth) or use demo credentials.
3. Upon first sign-in, an isolated personal workspace is automatically initialized via idempotent backend JIT provisioning, establishing a verified RS256 Bearer session token.
4. Protected application routes (`/dashboard`, `/assistant`, `/memory`, `/projects`, `/settings`) enforce strict authentication boundaries: unauthenticated visitors are redirected to `/login`.

#### Step 2: Ingest Ground Truth Memory (45s)
1. In the sidebar, select **Memory** -> **New Memory**.
2. Fill out the form:
   - **Title**: `Project Apollo Launch Timeline`
   - **Content**: `Apollo phase 1 kick-off scheduled for November 12. Security review requires three sign-offs.`
   - **Type**: `knowledge`
   - **Tags**: `apollo, timeline, security`
   - **Importance Score**: `0.8`
3. Click **Save Memory**. Observe the memory card appear and graph node register.

#### Step 3: Semantic Retrieval Without Exact Keyword Match (45s)
1. In the search box, search: `when is phase 1 starting?`
2. Press Enter. Notice that semantic embeddings retrieve the note based on meaning ("phase 1 starting" $\leftrightarrow$ "phase 1 kick-off scheduled"), returning a 100% relevant match.

#### Step 4: Grounded RAG Query with Evidence Citations (60s)
1. Click **Assistant** in the sidebar. Select **Grounded RAG** mode.
2. Ask: `What is the launch date for Apollo phase 1?`
3. **Observable Outcome**:
   - The assistant answers: *"Based on the verified context in your SynapseOS memory: Apollo phase 1 kick-off scheduled for November 12..."*
   - An expandable **Evidence Citation** badge appears: `[1] Project Apollo Launch Timeline (100% match)`.
   - The model attribution badge confirms: `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF • Simulation Mode`.

#### Step 5: Strict Abstention Verification (Zero Hallucination) (45s)
1. In the Assistant tab, ask: `What was the marketing budget allocated for Tokyo in 2024?`
2. **Observable Outcome**:
   - The system displays an **Evidence Insufficient** guard alert.
   - The assistant responds: *"I searched your SynapseOS memory, but could not find sufficient verified evidence to answer this question accurately."*
   - Zero hallucinated numbers or fabricated marketing figures.

#### Step 6: Consequential Agent Action & Human Approval Gate (60s)
1. Switch Assistant mode to **Agent Reasoning**.
2. Instruct the agent: `Please create a new project called Apollo Space Mission.`
3. **Observable Outcome**:
   - The agent formulates an `AgentPlan` (Goal: `Create new project`).
   - Recognizing that `create_project` is a consequential workspace mutation, execution **halts** with status `awaiting_approval`.
   - A high-visibility amber **Human Approval Required** barrier card renders with **Approve Execution** and **Reject** buttons.
4. Click **Reject**.
5. The agent acknowledges: *"Action 'Create project' was cancelled as requested."*
6. Check **Projects** in the sidebar: verify that no unauthorized project was created.

---

### Track C: 10-Minute Technical Architecture Deep-Dive

For technical judges evaluating code quality, security posture, and system architecture:
1. **Interactive OpenAPI Specs**: Review `https://synapseos-api-2onj.onrender.com/docs` for schemas, tags, response models, and HTTP status codes.
2. **Security Audit**: Review [`docs/PHASE_6_FINAL_AUDIT.md`](file:///c:/Users/Manya/Downloads/Projects/synapseos/docs/PHASE_6_FINAL_AUDIT.md) covering 19 passing security audit tests.
3. **Dual-Defense Authentication**: Inspect [`apps/api/app/routers/v1/auth.py`](file:///c:/Users/Manya/Downloads/Projects/synapseos/apps/api/app/routers/v1/auth.py) and [`apps/web/src/lib/api.ts`](file:///c:/Users/Manya/Downloads/Projects/synapseos/apps/web/src/lib/api.ts) for simultaneous HttpOnly cookie and Bearer header token fallback.
4. **Privacy Invariants**: Review [`docs/PRIVACY.md`](file:///c:/Users/Manya/Downloads/Projects/synapseos/docs/PRIVACY.md) and telemetry manager (`apps/api/app/core/llm/telemetry.py`), verifying that prompt texts and document contents are strictly excluded from logs and metrics.

---

## 4. Capability & Reality Matrix

| Feature / Subsystem | Status | Technical Reality |
| :--- | :---: | :--- |
| **Relational Memory Store** | `VERIFIED` | SQLite (`aiosqlite`) running on backend container with async session isolation. |
| **Vector Indexing & Retrieval** | `VERIFIED` | Local cosine-similarity vector store with workspace tenant boundaries. |
| **Knowledge Graph** | `VERIFIED` | Local graph node & edge registry with entity relationship linking. |
| **Evidence-Backed Citations** | `VERIFIED` | RAG pipeline extracts and validates citation indices against active memory IDs. |
| **Principled Abstention** | `VERIFIED` | Threshold guard returns explicit abstention message when evidence is missing. |
| **Agent Multi-Step Planner** | `VERIFIED` | Pydantic schema validation (`AgentPlan`, `AgentStep`) with reflection generation. |
| **Human-in-the-Loop Barrier** | `VERIFIED` | Consequential action approval sessions with 900s TTL and replay prevention. |
| **Live Nebius Inference** | `SIMULATION_VERIFIED` | Zero-cost deterministic simulation verified on live deployment. Free credits exhausted; zero-cost constraint strictly preserved. |
| **Storage Durability** | `EPHEMERAL` | Render free tier discards ephemeral disk files on cold reboot. $0 ongoing cost. |
| **Document Formats** | `VERIFIED` | `.txt`, `.md`, `.json`, `.csv`, and text-extractable `.pdf`. (Scanned OCR rejected with 400). |
