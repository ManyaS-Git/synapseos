# SynapseOS Phase 5.1 — Deployment & Hackathon Release Report

**Date**: 2026-10-23  
**Status**: `DEPLOYED_WITH_LIMITATIONS` (Live & Verified on Free Hosting)  
**Latest Git Release Commit**: `708c48a` on `origin/main`  
**Release Manager**: Autonomous Senior DevOps & Release Engineering Agent  

---

## 1. Public Endpoints & Service URLs

| Component | Target Free-Tier Host | Public URL / Deployment Target | Status |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** (Hobby Plan) | [https://synapseos-three.vercel.app](https://synapseos-three.vercel.app) | **LIVE** (HTTP 200, 115 KB Next.js 14 bundle) |
| **Backend API** | **Render** (Free Web Service) | [https://synapseos-api-2onj.onrender.com](https://synapseos-api-2onj.onrender.com) | **LIVE** (HTTP 200, Service ID: `srv-dbdm9tg473hc73cs3rf0`) |
| **API Docs (Swagger)** | Render | [https://synapseos-api-2onj.onrender.com/docs](https://synapseos-api-2onj.onrender.com/docs) | **LIVE** (Enabled for judges via `ENABLE_DOCS_IN_PRODUCTION=true`) |
| **Health Probe** | Render | [https://synapseos-api-2onj.onrender.com/health](https://synapseos-api-2onj.onrender.com/health) | **LIVE** (Responsive 200 OK probe endpoint) |
| **Readiness Probe** | Render | [https://synapseos-api-2onj.onrender.com/health/ready](https://synapseos-api-2onj.onrender.com/health/ready) | **LIVE** (HTTP 200, Status: `ready`, Engine: `sqlite`) |

---

## 2. Selected Zero-Cost Hosting Architecture

To ensure **100% genuine zero-cost hosting** without credit card entrapment, trial conversions, or accidental billing risks:

1. **Frontend: Vercel (Hobby Free Tier)**
   - **Cost**: $0.00 / month.
   - **Features**: Global Edge CDN, automated SSL/HTTPS, native Next.js 14 App Router support, automatic preview and production deployments from Git.
   - **Root Directory**: `apps/web`.
   - **Environment Configuration**: `NEXT_PUBLIC_API_URL` pointed to `https://synapseos-api-2onj.onrender.com`.
2. **Backend: Render (Free Web Service)**
   - **Cost**: $0.00 / month (512 MB RAM, 0.1 CPU).
   - **Features**: Free HTTPS termination, automatic git deploys via `render.yaml` Blueprint, automatic secret generation for `APP_SECRET_KEY` and `JWT_SECRET_KEY`.
   - **Root Directory**: `apps/api`.
   - **Runtime**: Python 3.12.
3. **Storage Strategy**: **Option B (Temporary Local Storage for Hackathon Demo)**
   - Render's free tier provides ephemeral filesystem storage.
   - The application runs in `STORAGE_MODE=local_embedded`, utilizing local async SQLite (`aiosqlite`), in-process vector indexing, and local file storage.
   - **Demo Warning**: Stored demo data resets when the free container restarts or cold sleeps. Real personal documents or production secrets must never be loaded.

---

## 3. Exact Build & Startup Commands

### Backend (Render Free Web Service)
- **Runtime**: Python 3.12
- **Build Command**:
  ```bash
  pip install -r apps/api/requirements.txt
  ```
- **Startup Command**:
  ```bash
  uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port $PORT --workers 1
  ```
- **Health Check Path**: `/health`

### Frontend (Vercel Hobby)
- **Framework**: Next.js 14
- **Root Directory**: `apps/web`
- **Build Command**:
  ```bash
  npm run build
  ```
- **Output Directory**: `.next`

---

## 4. Live Production End-to-End Verification Results

All automated verification gates were executed over the public Internet against the deployed HTTPS endpoints via `scripts/verify_live_deployments.py`:

| # | Test Check | Target URL | Result | Live Evidence / Diagnostic Details |
| :-: | :--- | :--- | :---: | :--- |
| 1 | **Frontend HTTPS Delivery** | `https://synapseos-three.vercel.app` | **PASS** | HTTP 200, Title: *"SynapseOS – The AI That Remembers, Reasons, and Acts"*, Size: 115,128 bytes |
| 2 | **CORS Preflight** | `https://synapseos-api-2onj.onrender.com/api/v1/auth/login` | **PASS** | HTTP 200, `Access-Control-Allow-Origin: https://synapseos-three.vercel.app`, `Credentials: true` |
| 3 | **Root API Probe** | `https://synapseos-api-2onj.onrender.com/` | **PASS** | HTTP 200, App: `SynapseOS API`, Version: `0.4.0` |
| 4 | **Health Probe** | `https://synapseos-api-2onj.onrender.com/health` | **PASS** | HTTP 200, `{'status': 'healthy'}` |
| 5 | **Liveness Probe** | `https://synapseos-api-2onj.onrender.com/health/live` | **PASS** | HTTP 200, `{'status': 'alive'}` |
| 6 | **Readiness Probe** | `https://synapseos-api-2onj.onrender.com/health/ready` | **PASS** | HTTP 200, `status: ready`, Storage engine: `sqlite` |
| 7 | **User Registration** | `POST /api/v1/auth/register` | **PASS** | HTTP 201, User created with valid UUID, HttpOnly session cookies issued |
| 8 | **Workspace Management** | `POST /api/v1/workspaces` | **PASS** | HTTP 201, Personal workspace created and bound to tenant session |
| 9 | **Memory Creation** | `POST /api/v1/memory?workspace_id=...` | **PASS** | HTTP 201, Memory created (`Apollo Mission Schedule`), embedding indexed |
| 10 | **Semantic Memory Search** | `POST /api/v1/memory/search` | **PASS** | HTTP 200, Query *"when is phase 1 starting?"* returned 1 grounded memory result |
| 11 | **RAG Grounded Query** | `POST /api/v1/rag/query` | **PASS** | HTTP 200, Citations: 1, `is_unsupported: False`, verified against persistent context |
| 12 | **RAG Principled Abstention**| `POST /api/v1/rag/query` | **PASS** | HTTP 200, Out-of-context query correctly abstained (`is_unsupported: True`, confidence: 0.0) |
| 13 | **Agent Approval Barrier** | `POST /api/v1/agent/chat` | **PASS** | Consequential request (`create_project`) safely paused with `status: awaiting_approval` |
| 14 | **Agent Rejection Safety Gate**| `POST /api/v1/agent/approve` | **PASS** | Action rejection consumed safely, step marked `skipped`, zero unauthorized side effects |
| 15 | **Auth Logout Invalidation** | `POST /api/v1/auth/logout` | **PASS** | HTTP 200, Session cookies cleared and invalidated |

---

## 5. Live Nebius Inference Status

- **Status**: `SIMULATION_VERIFIED`
- **Details**:
  - Live Nebius Token Factory API keys have not been configured on Render (`NEBIUS_API_KEY` is empty).
  - The deterministic offline simulation mode is active and verified (`scripts/verify_nebius_inference.py --allow-simulated`).
  - The UI and API responses transparently attribute all generations:
    - Attribution: `nvidia/nemotron-4-340b-instruct • Simulation Mode`
    - Response headers / JSON bodies explicitly flag `is_simulated: true` and `provider: simulation`.
    - Live badges are displayed only when an actual API key is present. Zero deceptive claims are made to evaluators.

---

## 6. Storage Durability & Backup Status

- **Storage Mode**: `local_embedded` (SQLite + Qdrant embedded + JSON Graph).
- **Durability**: **Ephemeral across cold reboots**.
- **Backup Support**: Supported locally via `python scripts/backup_restore.py backup`. Backups produce a timestamped tar archive containing the database, vector indexes, and encryption-at-rest metadata.

---

## 7. Free-Tier Limitations & Cold Start Accommodations

1. **Cold Starts (Render Free Tier)**:
   - Web services sleep after 15 minutes of inactivity. The first request after sleep experiences a **30 to 45 second wake-up delay**.
   - **Frontend Accommodation**:
     - Added an **API Status indicator** in the top navigation bar (`API Connected` / `Waking API...`).
     - Added a **Wake-Up Notice Banner** with an automated retry button and clear user messaging when the backend is spinning up.
     - Enhanced `api.ts` with custom timeout handling that explains free-tier cold starts rather than failing silently with `Failed to fetch`.
2. **Ephemeral Disk**:
   - Container restarts discard files written to local disk.
   - Evaluators are advised in `docs/HACKATHON_DEMO_GUIDE.md` to run test walkthroughs within an active session.

---

## 8. Teardown Instructions

To completely delete the deployed free services at any time:
- **Render**: Navigate to Dashboard -> `srv-dbdm9tg473hc73cs3rf0` -> **Settings** -> **Delete Web Service**.
- **Vercel**: Navigate to Project Settings -> **Delete Project**.
- Total ongoing cost: **$0.00**.
