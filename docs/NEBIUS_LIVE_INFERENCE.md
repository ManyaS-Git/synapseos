# Nebius Token Factory Live Inference Guide

**SynapseOS Phase 3: AI Infrastructure & Remote Model Integration**  
**Provider**: Nebius Token Factory  
**Console**: [https://tokenfactory.nebius.com/](https://tokenfactory.nebius.com/)  
**Inference Architecture**: OpenAI-Compatible Chat Completions (`/chat/completions`) & Models (`/models`)

---

## 1. Executive Summary

SynapseOS is architected to utilize **NVIDIA Nemotron** high-parameter reasoning models hosted on **Nebius Token Factory** for bounded agent planning, structured reflection, and grounded RAG synthesis.

When an API key is not configured or when `PRIVACY_MODE=local_only` is active, SynapseOS operates in **deterministic offline simulation mode**, ensuring local development and continuous integration suites run 100% offline without cost. When configured with valid Nebius credentials in `hybrid` mode, SynapseOS communicates with remote Nebius inference endpoints over TLS 1.3, providing verifiable provider attribution badges directly in the frontend UI.

---

## 2. Configuration & Verified API Contract

### Endpoint & Credentials
| Parameter | Setting / Value | Description |
|:----------|:----------------|:------------|
| **Provider** | Nebius Token Factory | Managed cloud inference platform |
| **API Base URL** | `https://api.tokenfactory.nebius.com/v1/` | Base URL for REST API |
| **Authentication** | `Authorization: Bearer <NEBIUS_API_KEY>` | Standard HTTP Bearer header |
| **Chat Endpoint** | `POST https://api.tokenfactory.nebius.com/v1/chat/completions` | OpenAI-compatible chat completions |
| **Model Catalog** | `GET https://api.tokenfactory.nebius.com/v1/models` | List available models & health |
| **Default Candidate Model** | `nvidia/nemotron-4-340b-instruct` | Primary 340B synthetic data & reasoning model |
| **Alternative Verified Models** | `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`, `meta-llama/Meta-Llama-3.1-70B-Instruct` | Configurable alternative models |
| **Default Privacy Mode** | `PRIVACY_MODE=hybrid` | Only prompts and authorized memory chunks egress |

### Supported Parameters
- `temperature`: Configured between `0.0` (health/verification) and `0.1` (RAG / planning).
- `max_tokens`: Bounded between 512 and 2048 to prevent runaway generation.
- `stream`: False (SynapseOS uses structured Pydantic model validation).
- `response_format`: Markdown JSON code fences with robust repair fallback.

---

## 3. Nebius Promotional Credit Redemption & Setup

The user may have received a Nebius Token Factory promotional credit offer:
- **Credit Amount**: 25 credits (confirm currency in console).
- **Redemption Deadline**: 31 December 2026.
- **Expiration Policy**: Once applied to an active account, redeemed credits do not expire.
- **Verification**: Billing address and payment card verification may require a temporary $0 authorization charge.

> [!IMPORTANT]
> **Manual User Action Required:**
> The promotional code is **NOT** an API key. For security, automated systems and agents cannot log into your Nebius account, enter credit cards, or redeem codes on your behalf. You must redeem the credit and create the API key manually.

### Step-by-Step Setup:
1. Navigate to the official Nebius Token Factory console: [https://tokenfactory.nebius.com/](https://tokenfactory.nebius.com/).
2. Sign in with your account credentials.
3. In the top-right profile menu, click **Top Up**.
4. Enter your promotional code and complete payment card verification if prompted ($0 temporary hold).
5. Confirm that your promotional balance displays 25 credits in the billing overview.
6. Open the **API Keys** section in the left navigation sidebar.
7. Click **Create API Key**, provide a label (e.g., `synapseos-beta`), and copy the key immediately.
8. Add the key to your server-side environment (`.env`):
   ```bash
   NEBIUS_API_KEY="your_actual_key_here"
   NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1/"
   NEBIUS_MODEL="nvidia/nemotron-4-340b-instruct"
   PRIVACY_MODE="hybrid"
   ```
9. **Never** commit your `.env` file or paste your API key into git, pull requests, or client-side bundles.

---

## 4. Live Verification CLI

SynapseOS provides a dedicated verification script to validate remote inference before launching the application:

```bash
# Test live cloud inference (requires NEBIUS_API_KEY in .env)
python scripts/verify_nebius_inference.py

# Test offline simulation mode (works with 0 credentials)
python scripts/verify_nebius_inference.py --allow-simulated
```

### Script Exit Statuses:
- `[STATUS: LIVE_PROVIDER_VERIFIED]` (Exit code 0): Real remote HTTP request succeeded, returned live Nemotron completion, and recorded telemetry.
- `[STATUS: SIMULATION_VERIFIED]` (Exit code 0 with `--allow-simulated`): Offline simulation passed. (Does **not** verify live inference).
- `[STATUS: BLOCKED]` (Exit code 2): `NEBIUS_API_KEY` is missing, empty, or placeholder.
- `[STATUS: FAILED]` (Exit code 1): Remote request returned an HTTP error (401, 404, 429) or timed out.

---

## 5. Security & Egress Boundaries

### What Leaves the Machine in Hybrid Mode (`PRIVACY_MODE=hybrid`):
1. **User Query**: The text prompt entered by the authenticated user.
2. **System Instruction**: Hardcoded SynapseOS reasoning guidelines and safety constraints.
3. **Workspace Context**: Top $K$ semantically matching memory excerpts retrieved *only* from the caller's authorized `workspace_id`.
4. **Tool Catalog**: Metadata describing available tools (`create_memory`, `create_project`).

### What Never Leaves the Machine:
1. **API Keys & Credentials**: Stored solely on the server in memory; sanitized from exception strings and telemetry.
2. **Databases & Indexes**: SQLite/PostgreSQL, Qdrant vectors, and Neo4j graphs remain 100% on local disk.
3. **Unrelated Memories**: Memories from other workspaces or unrelated to the query are strictly isolated.
4. **Full Document Bodies**: Document files remain in local storage; only indexed chunks are retrieved.

### Strict Air-Gapped Mode (`PRIVACY_MODE=local_only`):
Setting `PRIVACY_MODE=local_only` in `.env` activates an egress guard in `NebiusNemotronClient` that intercepts all calls and routes them to local simulation, ensuring zero external network packets are emitted.

---

## 6. Troubleshooting Guide

| Issue / Error | Probable Cause | Action |
|:--------------|:---------------|:-------|
| `401 Unauthorized` | Invalid, revoked, or expired API key | Check `NEBIUS_API_KEY` in `.env`; regenerate in Nebius console |
| `402 Payment Required` / `429 Insufficient Quota` | Account has 0 credit balance | Check balance in console; redeem promotional code via **Top Up** |
| `404 Not Found (Model not found)` | Model identifier is discontinued or misspelled | Verify model availability via `curl -H "Authorization: Bearer $KEY" https://api.tokenfactory.nebius.com/v1/models` and update `NEBIUS_MODEL` |
| `ConnectTimeout` / `ReadTimeout` | Network egress blocked or Nebius under high load | Verify internet connectivity; increase `NEBIUS_TIMEOUT_SECONDS=90.0` in `.env` |
| UI shows "Simulation Mode" badge | `NEBIUS_API_KEY` unset or invalid | Check `/health/ready` or backend logs for provider attribution |
