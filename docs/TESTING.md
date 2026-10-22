# SynapseOS Testing & Quality Assurance Guide

**Version**: 0.2.0  
**Test Status**: All Suites Green (52 Passed, 1 Skipped, 0 Failed)  

SynapseOS employs a multi-tiered testing strategy covering unit tests, mocked provider tests, live API endpoints, production frontend builds, and a comprehensive automated benchmark evaluation suite.

---

## 1. Test Execution Commands

### A. Run Backend Unit & Integration Tests (Pytest)
```bash
# Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # Linux / macOS

# Run full test suite with verbose output
pytest -v apps/api/tests

# Run specific test modules
pytest -v apps/api/tests/test_nebius.py
pytest -v apps/api/tests/test_rag.py
pytest -v apps/api/tests/test_agent.py
pytest -v apps/api/tests/test_memory_upload.py
```

### B. Run End-to-End Acceptance Test
```bash
python scripts/e2e_acceptance_test.py
```
Exercises 8 live API steps: health, registration, login/JWT, workspace tenancy, memory creation, document ingestion, evidence-backed RAG, strict abstention, and consequential agent approval.

### C. Run the Comprehensive Benchmark & Evaluation Suite
```bash
python scripts/evaluate_rag_agent.py
```
Outputs verifiable evaluation metrics and writes results to `scripts/evaluation_results.json`.

### D. Verify Nebius Provider & NVIDIA Nemotron Integration
```bash
# Safe verification in offline simulated mode
python scripts/verify_nebius_inference.py --allow-simulated

# Live inference verification (after setting NEBIUS_API_KEY in .env)
python scripts/verify_nebius_inference.py
```

### E. Run Frontend Type Checking & Production Build
```bash
# In project root
npm run build -w @synapseos/web
```

---

## 2. Test Catalog & Module Breakdown

| Test File | Test Cases | Scope & Guarantees |
|:----------|:----------:|:-------------------|
| **`test_auth.py`** | 11 | User registration, duplicate email rejection, Argon2id/bcrypt password hashing, login, JWT issuance, profile retrieval, refresh token lifecycle. |
| **`test_workspaces.py`** | 8 | Workspace creation, slug uniqueness, list filtering, owner permissions, member authorization boundaries. |
| **`test_projects.py`** | 7 | Project creation, duplicate name detection, update, archive status, deletion within workspace. |
| **`test_health.py`** | 3 | API root (`/`), health check endpoint (`/health`), and liveness ping (`/health/live`). |
| **`test_nebius.py`** | 5 | Nebius client initialization, deterministic completion, Pydantic structured output validation, health check reporting, and live integration smoke test (skipped when `NEBIUS_API_KEY` is not set). |
| **`test_rag.py`** | 3 | Grounded answers with source citations, strict abstention when evidence is absent, and cross-workspace isolation. |
| **`test_agent.py`** | 7 | Tool registry schema validation, consequential tool approval pausing, execution upon human confirmation, execution abortion on human rejection, safe tool auto-execution, reflection generation, **SSRF protection on web research**, and **cross-user approval prohibition (ForbiddenException)**. |
| **`test_memory_upload.py`** | 9 | Markdown and plain text file upload, chunking and metadata extraction, unsupported format rejection (400), empty file rejection (400), **JSON syntax validation and parsing**, **malformed JSON rejection**, **CSV row reading and structure extraction**, **empty CSV rejection**, **scanned PDF explicit OCR notification**, and **valid PDF multi-page extraction**. |

---

## 3. Evaluation Benchmark Suite (`scripts/evaluate_rag_agent.py`)

The evaluation script tests the end-to-end memory-to-action workflow against 8 realistic benchmark knowledge items across 9 distinct query categories:

1. **Answerable Domain Queries**: Tests retrieval recall (Recall@K) and citation accuracy.
2. **Disambiguation Queries**: Tests disambiguating active information from deprecated or superseded records.
3. **Out-of-Domain Abstention**: Tests the Abstention Guard to verify the system refuses to hallucinate facts outside its stored context.
4. **Safe Action Auto-Execution**: Tests autonomous planning and safe tool execution (`search_knowledge`).
5. **Consequential Action Approval**: Tests the human-in-the-loop safety gate for consequential tools (`create_project`).
6. **Consequential Action Rejection**: Tests that user rejection cleanly aborts execution and marks steps skipped.
7. **Post-Action Reflection**: Tests automatic synthesis and creation of observation memories.

### Measured Metrics Summary
- **Retrieval Recall@K**: **100.0%** (6/6)
- **Grounded Answer & Citation Rate**: **100.0%** (6/6)
- **Abstention Rate on Unsupported Facts**: **100.0%** (3/3)
- **Safe Tool Execution Rate**: **100.0%** (1/1)
- **Consequential Approval Gate**: **100.0%** (1/1)
- **Consequential Rejection Guard**: **100.0%** (1/1)
- **Reflection Generation Rate**: **100.0%**
- Results exported to: `scripts/evaluation_results.json`
