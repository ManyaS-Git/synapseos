# SynapseOS Privacy & Data Governance Architecture

**Version**: 0.2.0  
**Last Updated**: 2026-10-21  

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

| Data Category | Primary Storage | Storage Location | Encryption / Isolation |
|:--------------|:----------------|:-----------------|:-----------------------|
| **Auth & Metadata** | PostgreSQL 16 | Local container or host disk | Row-level tenant isolation by `workspace_id` |
| **Vector Index** | Qdrant | Local container or host memory | Collection-level namespacing by workspace |
| **Knowledge Graph** | Neo4j 5.x | Local container or host memory | Node property labeling by `workspace_id` |
| **Session Cache** | Redis 7.x | Local container or host memory | Ephemeral key TTLs with workspace prefix |

By default, in both Docker and standalone local installations, **all four databases reside entirely on the user's host infrastructure**.

---

## 3. Local Processing vs. External Transmission

SynapseOS supports three explicit inference routing modes (configurable in `.env` and `/settings`):

### Mode 1: Local-First (Offline / Air-Gapped)
- **Embedding Generation**: Local Ollama or local deterministic semantic tokenizer.
- **Reasoning & Planning**: Local Ollama instance (`llama3.2` or quantized edge models).
- **External Network Egress**: **Zero bytes**. No prompts, documents, or metadata leave your local machine.

### Mode 2: Hybrid Cloud (Default Hackathon Mode)
- **Persistent Storage**: 100% Local (PostgreSQL, Qdrant, Neo4j).
- **Embedding Generation**: Local.
- **Inference & RAG Synthesis**: Server-side request to **Nebius Token Factory** (`https://api.tokenfactory.nebius.com/v1/`) running `nvidia/nemotron-4-340b-instruct`.
- **Egress Boundary**: Only the user prompt, retrieved context snippets relevant to that specific question, and tool descriptions are transmitted over TLS 1.3 to Nebius Token Factory for inference.

### Mode 3: Cloud Accelerated
- Nebius GPU clusters process high-throughput agent loops and embeddings.

---

## 4. Client-Side Sanitization & Zero Prompt Logging

To protect sensitive information when external cloud inference is enabled:
1. **Zero Prompt Logging**:
   - `NebiusNemotronClient` explicitly excludes raw user prompts, private document contents, and completion bodies from application logs.
   - Server logs record only non-sensitive telemetry: HTTP status code, request duration in milliseconds, token counts, and model identifier.
2. **Client-Side Redaction**:
   - Configurable regex filters redact API keys, JWT tokens, credentials, and common PII patterns before payload construction.
3. **No Training on User Data**:
   - Nebius Token Factory endpoints operate under enterprise zero-data retention agreements; inference requests are not used to train public models.

---

## 5. Deletion & Retention

1. **Soft Deletion**:
   - Calling `DELETE /api/v1/memory/{id}` marks the memory status as `ARCHIVED` or `DELETED`, instantly removing it from active RAG retrieval, vector search results, and agent context.
2. **Hard Purging**:
   - Database cascading rules remove associated vectors from Qdrant and relationship nodes from Neo4j upon physical deletion.
3. **Approval Sessions**:
   - Consequential action approval sessions in `PENDING_SESSIONS` expire automatically after 10 minutes and are wiped from memory.

---

## 6. Known Limitations & What Is NOT Currently Guaranteed

- **Multi-Tenant Public Hosting**: In the current version, workspace isolation is enforced logically at the application and query layer (`workspace_id` filtering in SQLAlchemy). Physical database separation per tenant is not implemented.
- **End-to-End Client Encryption**: Data at rest in PostgreSQL and Qdrant is unencrypted unless underlying host volume encryption (e.g., BitLocker, LUKS) is enabled by the administrator.
- **Air-Gapped Cloud Mode**: Hybrid mode requires outbound internet connectivity to `api.tokenfactory.nebius.com`. If you require 100% air-gapped security, you must select **Local-First Only** in Settings.
