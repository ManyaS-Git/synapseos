# SynapseOS — Hackathon Demo Guide

This guide is designed for hackathon judges, evaluators, and reviewers exploring the live deployment of SynapseOS.

---

## 1. Overview & Architecture

SynapseOS is a memory-first personal AI environment featuring:
- **Persistent Memory & Graph**: Semantic retrieval, tagging, importance scoring, and visual knowledge graphs.
- **RAG with Citations & Abstention**: Context-grounded retrieval from ingested documents with traceable evidence and principled abstention when information is missing.
- **Safety-Bounded AI Agents**: Autonomous tool execution protected by human-in-the-loop approval barriers for consequential actions.
- **Privacy-Conscious Telemetry**: Zero logging of private prompts, tokens, or completions.

### Deployed Free-Tier Stack
- **Frontend**: Next.js 14 App Router on **Vercel** (Hobby Free Tier)
- **Backend**: FastAPI + SQLite/Vector/Graph engine on **Render** (Free Web Service)
- **Model Attribution**: Explicitly labelled simulated inference (NVIDIA Nemotron / Llama-3.3-70B-Instruct contract) when external API keys are not provisioned, ensuring 100% honesty and zero deceptive generation.

---

## 2. Cold-Start Notice (Free Hosting)

> [!NOTE]
> **Free-Tier Wake-Up Delay**:
> Render's free tier spins down after 15 minutes of inactivity. When accessing the application for the first time, the backend may take **30 to 45 seconds** to wake up.
> The UI includes an **API Status indicator** in the top navigation bar (`API Connected` / `Waking API...`) and a recovery banner that automatically detects wake-up and allows one-click retries.

---

## 3. Recommended 10-Step Judge Walkthrough

### Step 1: Open the Application
Navigate to the live public frontend URL:
- **Landing Page**: Review the feature overview, privacy architecture, and security model.
- Click **Launch SynapseOS** or **Get Started**.

### Step 2: Register a Dedicated Demo Account
- Click **Sign Up** on the login screen.
- Enter synthetic demo credentials:
  - **Full Name**: `Judge Demo`
  - **Username**: `judge_demo`
  - **Email**: `judge@demo.local`
  - **Password**: `JudgeDemoPass123!`
- The system automatically creates a personal workspace and signs you in via secure, HttpOnly session cookies.

### Step 3: Create a Memory
- Go to the **Memory** tab.
- Click **New Memory**.
- Title: `Project Apollo Launch Timeline`
- Content: `Apollo phase 1 kick-off scheduled for November 12. Security review requires three sign-offs.`
- Tags: `project, timeline, security`
- Importance: `4`
- Click **Save**. Observe the real-time addition to the memory list and memory health score update.

### Step 4: Semantic Search
- In the search bar on the Memory view, type: `when is phase 1 starting?`
- Press Enter. Observe semantic retrieval matching the concept of "timeline" even without identical keywords.

### Step 5: Upload a Document
- Navigate to the **Documents** tab.
- Prepare a small synthetic `.txt` or `.md` file, for example `project_spec.txt`:
  ```
  Project SynapseOS Architecture Spec
  Confidentiality: Tier 1 Internal
  Primary Ingestion Port: 8000
  Fallback Strategy: Bounded Local Simulation
  Audit Frequency: Weekly automated integrity scans.
  ```
- Drag and drop or browse to upload `project_spec.txt`.
- Observe document parsing, chunking, and embedding into the local vector index.

### Step 6: Grounded RAG Query
- Navigate to the **Assistant** tab.
- Ask: `What is the audit frequency specified in the project spec?`
- **Expected Outcome**:
  - The assistant responds: *"According to the project specification, the audit frequency is weekly automated integrity scans."*
  - The response includes an expandable **Citation pill** referencing `project_spec.txt` chunk 0 with similarity score.
  - The attribution badge displays: `nvidia/nemotron-4-340b-instruct • Simulation Mode` (transparently attributed).

### Step 7: Principled Abstention
- In the Assistant tab, ask a question not present in the workspace or document:
  `What was the total budget approved for the Tokyo marketing event in 2024?`
- **Expected Outcome**:
  - The assistant explicitly abstains: *"I cannot answer this question based on the retrieved context, as the provided documents and memories do not contain information about marketing budgets."*
  - No hallucinations or fabricated data.

### Step 8: Trigger Consequential Agent Action
- In the Assistant tab, instruct the agent:
  `Please delete the Apollo Launch Timeline memory.`
- **Expected Outcome**:
  - The agent formulates a plan, identifies that `delete_memory` is a consequential action, and halts execution before running it.
  - A modal / action approval card appears:
    - **Action**: `delete_memory`
    - **Target**: Apollo Launch Timeline
    - **Risk**: Consequential / Irreversible

### Step 9: Verify Human-in-the-Loop Barrier
- Click **Reject** or **Approve**.
- If rejected: The agent acknowledges that the human operator denied permission and leaves the memory intact.
- If approved: The agent safely deletes the memory and confirms execution.
- Review the **Activity** tab to see the immutable audit event logged with timestamp and decision.

### Step 10: Logout & Session Invalidation
- Click profile settings in the upper right.
- Click **Log Out**.
- Verify that session cookies are cleared and attempting to visit `/dashboard` redirects immediately to `/login`.

---

## 4. Known Free-Tier Limitations

1. **Ephemeral Local Storage (Option B)**:
   - On Render free tier, disk storage is non-persistent across container redeployments and cold sleep restarts.
   - Demo memories and uploaded documents may reset if the service restarts.
   - **Do not store confidential or production secrets in the demo environment.**
2. **Cold Starts**:
   - Inactivity causes a ~30-45 second wake-up period on the next incoming request.
3. **Model Attribution**:
   - In the absence of an external paid API key, responses are generated using the deterministic simulation contract (`is_simulated: true`). The UI transparently labels all simulated responses to prevent deceptive generation.
4. **Scanned Documents (OCR)**:
   - Scanned image-only PDFs without extractable text streams are rejected with HTTP 400 (OCR is not implemented in this tier). Plain text, markdown, and structured text PDFs are supported.
