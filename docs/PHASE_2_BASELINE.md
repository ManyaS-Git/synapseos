# SynapseOS Phase 2 Baseline Report

**Audit Date:** October 22, 2026  
**Auditor:** Principal Engineer, AI Infrastructure Engineer, Application Security Engineer, Release QA Lead  
**Repository State:** Commit `a320132` (Branch `main`, clean working tree)  

---

## 1. Executive Summary of Baseline State

SynapseOS has been audited across all core subsystems (FastAPI backend, Next.js 14 web client, Nebius Token Factory client, persistent memory, RAG pipeline, and bounded agent runtime). 

The baseline checks reproduce the following results:
- **Backend Unit & Integration Tests (`apps/api/tests/`):** 52 passed, 1 skipped in 27.45s.
- **End-to-End Live HTTP Acceptance (`scripts/e2e_acceptance_test.py`):** 8/8 steps passed.
- **Full-Stack API Contract Tests (`tests/integration/test_frontend_fullstack_contracts.py`):** 12/12 contracts verified in 62.23s.
- **RAG & Agent Benchmark Suite (`scripts/evaluate_rag_agent.py`):** 9/9 scenarios passed (100% metrics reported), but runtime warnings and mock coroutine errors were detected in sections 2–4.
- **Nebius Inference Verification (`scripts/verify_nebius_inference.py`):**
  - Unflagged run exits with status 2 (`[RESULT: UNCONFIGURED]`) because `NEBIUS_API_KEY` is not present in `.env`.
  - Flagged `--allow-simulated` run passes offline simulation.
- **TypeScript Typecheck (`npx tsc --noEmit`):** 0 errors.
- **Next.js Production Build (`npm run build -w @synapseos/web`):** 14/14 static & dynamic routes compiled clean.

---

## 2. Baseline Verification Commands & Exact Observed Results

### 2.1 Backend Pytest Suite
- **Command:** `.\.venv\Scripts\pytest.exe apps/api/tests/ -q`
- **Exit Code:** `0`
- **Output:**
  ```text
  ..................................s..................                    [100%]
  52 passed, 1 skipped in 27.45s
  ```
- **Observations:** The 1 skipped test is `test_nebius.py::test_nebius_live_inference_call`, which correctly skips when `NEBIUS_API_KEY` is empty.

### 2.2 Nebius Token Factory Live Verification
- **Command:** `.\.venv\Scripts\python.exe scripts\verify_nebius_inference.py`
- **Exit Code:** `1` (or status code 2)
- **Output:**
  ```text
  ========================================================================
     NEBIUS TOKEN FACTORY & NVIDIA NEMOTRON LIVE VERIFICATION
  ========================================================================

  [1/4] Inspecting Provider Configuration:
    Endpoint Base URL: https://api.tokenfactory.nebius.com/v1
    Target Model ID:   nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
    API Key Status:    <NOT SET>
    Require Live Call: True

  [RESULT: UNCONFIGURED]
    NEBIUS_API_KEY is not set or contains a placeholder value.
  ```
- **Command (Simulated):** `.\.venv\Scripts\python.exe scripts\verify_nebius_inference.py --allow-simulated`
- **Exit Code:** `0`
- **Output:**
  ```text
  [PASS - SIMULATED] Deterministic simulation verified successfully.
  ```
- **Discrepancy:** The script does not yet output standard machine-readable status tokens (`LIVE_PROVIDER_VERIFIED`, `SIMULATION_VERIFIED`, `BLOCKED`, `FAILED`).

### 2.3 Live End-to-End Acceptance Suite
- **Command:** `.\.venv\Scripts\python.exe scripts\e2e_acceptance_test.py`
- **Exit Code:** `0`
- **Output:**
  ```text
  [Step 1/8] Verifying Health & Liveness Endpoints... [PASS]
  [Step 2/8] Testing User Registration & JWT Authentication... [PASS]
  [Step 3/8] Verifying Workspace Tenancy... [PASS]
  [Step 4/8] Testing Persistent Memory Creation & Vectorization... [PASS]
  [Step 5/8] Testing Document Upload & Ingestion (.md)... [PASS]
  [Step 6/8] Testing Evidence-Backed RAG with Citations... [PASS]
  [Step 7/8] Testing Strict Abstention on Unsupported Questions... [PASS]
  [Step 8/8] Testing Agent Planning & Consequential Approval Gate... [PASS]
  ALL 8 END-TO-END ACCEPTANCE STEPS PASSED SUCCESSFULLY!
  ```

### 2.4 Full-Stack Frontend/Backend Contracts
- **Command:** `.\.venv\Scripts\pytest.exe tests/integration/test_frontend_fullstack_contracts.py -v -s`
- **Exit Code:** `0`
- **Output:**
  ```text
  [Contract 1/12] Health live check...
  [Contract 2/12] User registration...
  [Contract 3/12] Login & JWT session...
  [Contract 4/12] Workspace tenancy...
  [Contract 5/12] Memory creation & vectorization...
  [Contract 6/12] Memory listing & pagination...
  [Contract 7/12] Document multipart upload (.md)...
  [Contract 8/12] Evidence-backed RAG citations...
  [Contract 9/12] Strict abstention guard...
  [Contract 10/12] Agent planning & consequential gate...
  [Contract 11/12] Consequential action approval...
  [Contract 12/12] Memory deletion...
  [PASS] All 12 full-stack contracts successfully verified!
  1 passed in 62.23s
  ```

### 2.5 RAG & Agent Benchmark Evaluation
- **Command:** `.\.venv\Scripts\python.exe scripts\evaluate_rag_agent.py`
- **Exit Code:** `0`
- **Reported Metrics:**
  - Total Queries: 9
  - Retrieval Recall@K: 100% (6/6)
  - Grounded Citations: 100% (6/6)
  - Abstention: 100% (3/3)
  - Safe Tool Execution: 100% (1/1)
  - Consequential Gate: 100% (1/1)
  - Rejection Guard: 100% (1/1)
- **Observed Failures / Warnings in Logs:**
  - `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited`
  - `[error] Step execution failed error='coroutine' object has no attribute 'id' step=2`
  - `[warning] Failed to persist reflection memory error='coroutine' object has no attribute 'id'`
  - Only 9 queries tested, which does not provide comprehensive statistical evaluation.

### 2.6 Frontend Compilation & Typechecking
- **Command:** `npx tsc --noEmit` in `apps/web/`
  - **Exit Code:** `0` (Zero TypeScript diagnostics)
- **Command:** `npm run build -w @synapseos/web`
  - **Exit Code:** `0` (14/14 routes compiled into static and dynamic pages)

---

## 3. Implementation vs. Documentation Discrepancies

1. **Storage Durability:**
   - Documentation states that PostgreSQL, Qdrant, Neo4j, and Redis are the core storage tiers.
   - When running on a standalone developer machine without Docker daemons running:
     - SQLite is used as a fallback in tests via dependency override, but the primary API defaults to PostgreSQL connection failure on startup.
     - Qdrant falls back to in-memory `LocalVectorStore` without disk persistence, meaning embeddings are lost across process restarts if Qdrant is offline.
     - Agent approval sessions in `PENDING_SESSIONS` are stored in a process-local Python dictionary `dict[str, dict[str, Any]]`, which is volatile and not shared across workers or restarts.
2. **Evaluation Suite Scope:**
   - Previous reports claimed 100% benchmark results, but the benchmark only evaluated 9 canned test cases and suffered from mock unawaited coroutine errors during tool execution and reflection.
3. **Nebius Provider Error Resilience:**
   - While `apps/api/app/core/llm/nebius.py` handles HTTP errors with basic retries, it lacks dedicated unit test coverage for upstream edge cases (HTTP 401 unauthorized, 429 rate limits, 504 gateway timeouts, malformed upstream JSON).

---

## 4. Phase 2 Hardening Plan & Priority Order

- **Phase B:** Harden Nebius client, add mocked provider error tests, update verification script to output exact status tokens (`LIVE_PROVIDER_VERIFIED`, `SIMULATION_VERIFIED`, `BLOCKED`, `FAILED`).
- **Phase C:** Implement persistent local storage adapter for memories and vectors so that data survives process restarts in local development mode without requiring distributed cloud infrastructure.
- **Phase D:** Expand RAG evaluation dataset to 50+ diverse test cases (including prompt injection, conflicting docs, semantic paraphrases, multi-workspace isolation) and eliminate mock warnings.
- **Phase E:** Implement durable, concurrency-safe approval session store with TTL expiry and replay protection.
- **Phase F:** Conduct deep security audit on auth, tenant boundaries, SSRF, and file upload validation.
- **Phase G & H:** Verify end-to-end frontend-to-backend flows and document honest feature status.
- **Phase I & J:** Final verification and comprehensive Phase 2 verification report.
