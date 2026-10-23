# SynapseOS Privacy & Data Governance Architecture

**Version**: 0.4.0 (Phase 4 — Private Beta)  
**Last Updated**: 2026-10-22  

SynapseOS is engineered from first principles around **user data ownership, transparency, and minimal external exposure**. This document outlines our data lifecycle, privacy boundaries, logging policies, and external transmission disclosures.

---

## 1. What Information Is Stored

SynapseOS stores:
1. **User Identity & Authentication**:
   - Username, email address, password hash (hashed using Argon2id).
   - Session timestamps and JWT signatures.
2. **Workspaces & Projects**:
   - Workspace names, slugs, user role mappings, and project groupings.
3. **Memories & Documents**:
   - Text contents of notes, conversation summaries, decisions, tasks, and uploaded files (`.txt`, `.md`, `.pdf`, `.json`, `.csv`).
   - Derived metadata: title, tags, importance score, memory type, source attribution, and timestamps.
4. **Vector Embeddings**:
   - 768-dimensional normalized floating-point embeddings computed from memory chunks.
5. **Knowledge Graph Entities**:
   - Node representations of memories and typed relationship edges (e.g., `RELATES_TO`, `DERIVED_FROM`).
6. **Agent Execution History & Audit Logs**:
   - Structured plan goals, steps, tool arguments, human approval decisions (approved/rejected), and execution status.

---

## 2. Where Data Is Stored

| Data Category | Standalone / Beta Storage | Distributed Storage | Storage Location | Encryption / Isolation |
|:--------------|:--------------------------|:--------------------|:-----------------|:-----------------------|
| **Auth & Metadata** | SQLite (`synapseos_local.db`) | PostgreSQL 16 | Local volume or disk | Row-level tenant isolation by `workspace_id` |
| **Vector Index** | Local JSON index (`local_vector_store.json`) | Qdrant 1.10 | Local volume or disk | Workspace-scoped filtering in vector queries |
| **Knowledge Graph** | Local JSON graph (`local_graph_store.json`) | Neo4j 5.x | Local volume or disk | Node property labeling by `workspace_id` |
| **Session & Approvals** | Durable JSON (`approval_sessions.json`) | Redis 7.x | Local volume or disk | Ephemeral key TTLs (900s) + replay protection |

By default, in both Docker and standalone local installations, **all persistent databases reside entirely on the user's host infrastructure**.


---

## 3. Local Processing vs. External Transmission

SynapseOS supports three explicit inference routing modes (configurable in `.env` and `/settings`):

### Mode 1: Local-First (Offline / Air-Gapped) — `PRIVACY_MODE=local_only`
- **Embedding Generation**: Local deterministic semantic tokenizer / embedding model.
- **Reasoning & Planning**: Local deterministic simulation or local edge runner.
- **External Network Egress**: **Strictly Zero Bytes**. Even if an API key is configured in the environment, `NebiusNemotronClient` intercepts all outbound requests and executes local simulation. No packets leave the machine.

### Mode 2: Hybrid Privacy (Default / Beta Ready) — `PRIVACY_MODE=hybrid`
- **Important Disclosure**: **Hybrid mode is NOT fully local.** In hybrid mode, specific data is transmitted to Nebius Token Factory over encrypted TLS 1.3.
- **Persistent Storage**: 100% Local (PostgreSQL/SQLite, local vector store, local knowledge graph).
- **Embedding Generation**: Local (embeddings are generated on-device, never transmitted).
- **Inference & RAG Synthesis**: Server-side HTTPS POST to `https://api.tokenfactory.nebius.com/v1/chat/completions` running `nvidia/nemotron-4-340b-instruct`.
- **Egress Boundary**:
  - **Transmitted to Nebius**: The user's prompt query, system prompt instructions, and top $K$ retrieved memory excerpts (scoped strictly to the user's authorized workspace).
  - **Never Transmitted**: Database credentials, passwords, JWT secrets, Nebius API keys, full documents, or memories from outside the active workspace.
- **Pre-Retrieval Authorization**: The backend validates workspace membership (`WorkspaceRepository.is_member`) *before* executing vector search or prompt assembly, guaranteeing that cross-workspace data can never reach external model context.

### Mode 3: Cloud Accelerated — `PRIVACY_MODE=cloud_only`
- Unbounded cloud inference with cloud-hosted vector indexes and remote embeddings. (Currently marked as non-default / beta optional).

---

## 4. Privacy-First Observability & Zero Key Leakage

To preserve strict privacy standards while maintaining operational visibility:
1. **Server-Side Credential Containment**:
   - `NEBIUS_API_KEY` is loaded exclusively on the backend into memory. It is never exposed in frontend bundles, HTML, local storage, API responses, or error messages.
   - Any API error string matching the key pattern is sanitized to `[REDACTED_API_KEY]`.
2. **Zero Prompt Telemetry**:
   - `LLMTelemetryManager` records only non-content operational telemetry: request ID, model identifier, provider name, latency in milliseconds, prompt tokens, completion tokens, retry attempts, and HTTP status codes.
   - User prompt content, document text, and completion text are strictly excluded from telemetry stores and logs.
3. **Transparent Provider Attribution**:
   - Every assistant and RAG response returned to the client includes explicit metadata flags: `is_simulated`, `is_fallback`, `provider`, and `model_used`.
   - The frontend renders an explicit badge distinguishing "Live Nebius AI" from "Simulation Mode" or "Fallback", ensuring simulated answers can never be mistaken for real model inference.

---

## 5. Deletion & Retention

1. **Soft Deletion**:
   - Calling `DELETE /api/v1/memory/{id}` marks the memory status as `ARCHIVED` or `DELETED`, instantly removing it from active RAG retrieval, vector search results, and agent context.
2. **Hard Purging**:
   - Database cascading rules remove associated vectors from the local index and relationship nodes from the graph upon physical deletion.
3. **Approval Sessions**:
   - Consequential action approval sessions in `approval_store` expire automatically after 10 minutes (TTL enforced) and are wiped upon consumption or rejection.

---

## 6. Known Limitations & What Is NOT Currently Guaranteed

- **Multi-Tenant Public Hosting**: Workspace isolation is enforced logically at the application and query layer (`workspace_id` filtering in SQLAlchemy). Physical database separation per tenant is not implemented.
- **End-to-End Client Encryption**: Data at rest in SQLite/PostgreSQL is unencrypted unless underlying host volume encryption (e.g., BitLocker, LUKS) is enabled by the administrator.
- **Air-Gapped Cloud Mode**: Hybrid mode requires outbound internet connectivity to `api.tokenfactory.nebius.com`. If you require 100% air-gapped security, you must set `PRIVACY_MODE=local_only` in `.env`.

