# Clerk Authentication Setup & Identity Integration Guide — SynapseOS

This guide describes the integration of **Clerk** as the primary authentication and identity provider for SynapseOS, while preserving SynapseOS's existing internal architecture, visual design, data boundaries, and security guarantees.

---

## 1. Authentication Architecture: Before and After

| Component | Before (Local Auth) | After (Clerk + Dual-Mode Verification) |
| :--- | :--- | :--- |
| **Identity Provider** | Local database (`users.password_hash` with Argon2) | **Clerk** (OAuth, Passwordless, Socials, MFA) |
| **Frontend Auth SDK** | Custom React hooks with manual fetch & `localStorage` | **`@clerk/nextjs` (v5)** with App Router integration |
| **Route Protection** | Client-side `useEffect` redirect | Next.js Edge **`clerkMiddleware`** + Route Matcher |
| **Sign-in / Sign-up** | Custom forms on `/login` and `/register` | Official Clerk `<SignIn />` and `<SignUp />` with custom dark theme tokens |
| **Session Token** | HS256 JWT signed with local `JWT_SECRET_KEY` | RS256 asymmetric JWT signed by Clerk's private key |
| **Backend Verification** | Symmetric HS256 secret key verification | **Cryptographic RS256 signature verification** via PEM public key (`CLERK_JWT_KEY`) or cached JWKS (`CLERK_JWKS_URL`) |
| **Identity Mapping** | Direct lookup by internal UUID | Verified `clerk_user_id` mapped to internal `User` UUID |
| **User Provisioning** | Manual `/auth/register` API call | **Idempotent first-login JIT provisioning** with default personal workspace |
| **Tenant Isolation** | Workspace membership checks (`user_id == member.user_id`) | **Preserved 100%**: all workspaces, memories, graphs, RAG queries, and approvals remain scoped to internal UUID |
| **Backward Compatibility** | Standard test tokens | Full dual-mode support (local test tokens continue to authenticate seamlessly in CI/automated test suites) |

---

## 2. Free-Tier Suitability & Boundaries ($0 Budget)

Clerk provides an extensive **Free (Hobby) Tier**:
- **Monthly Active Users (MAU):** Up to **10,000 MAUs** included at **$0.00 / month**.
- **Social Connections:** Google, GitHub, and email/password authentication included with no payment method required.
- **Session Tokens & JWKS:** Unlimited JWT verification requests against public JWKS.
- **Budget Compliance:** SynapseOS runs completely within the $0.00 budget. Do not activate paid add-ons, enterprise features, or enter credit card information.

---

## 3. Step-by-Step Clerk Dashboard Setup

Follow these exact steps in the Clerk Dashboard to obtain your credentials:

1. **Create Clerk Account & Application**:
   - Go to [https://dashboard.clerk.com](https://dashboard.clerk.com) and sign in or sign up.
   - Click **Add application**.
   - Name the application: `SynapseOS`.
   - Select authentication methods (e.g., **Email**, **Google**, **GitHub**).
   - Click **Create application**.

2. **Copy API Keys**:
   - In the Clerk Dashboard sidebar, navigate to **Configure > Developers > API Keys**.
   - Copy the **Publishable key** (`pk_test_...` or `pk_live_...`).
   - Copy the **Secret key** (`sk_test_...` or `sk_live_...`).

3. **Get PEM Public Key (Recommended for Zero-Latency Backend Verification)**:
   - In the Clerk Dashboard, navigate to **Configure > Developers > API Keys**.
   - Under the **JWT Public Key** section, click **Show JWT Public Key** or **Copy public key**.
   - You can supply this as `CLERK_JWT_KEY` in Render/local environment.

4. **Configure Allowed Redirect URLs (for Production)**:
   - In **Configure > Paths**, verify:
     - Sign-in path: `/login`
     - Sign-up path: `/register`
     - After sign-in: `/dashboard`
     - After sign-up: `/dashboard`

---

## 4. Local Development Environment Configuration

### Frontend (`apps/web/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key
CLERK_SECRET_KEY=sk_test_your_secret_key
```

### Backend (`apps/api/.env`):
```env
# Clerk Verification Settings
CLERK_SECRET_KEY=sk_test_your_secret_key
CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key
# Either provide the PEM key directly:
CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
# Or provide the instance issuer:
CLERK_ISSUER=https://your-app-id.clerk.accounts.dev
```

---

## 5. Cloud Deployment Setup (Vercel & Render)

### A. Vercel (Frontend: `https://synapseos-three.vercel.app`)
1. Open your Vercel Dashboard and select the **`synapseos`** project.
2. Go to **Settings > Environment Variables**.
3. Add the following variables (for Production & Preview):
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: `pk_live_...` (or `pk_test_...`)
   - `CLERK_SECRET_KEY`: `sk_live_...` (or `sk_test_...`)
4. Trigger a redeploy (or push to `main`).

### B. Render (Backend: `https://synapseos-api-2onj.onrender.com`)
1. Open your Render Dashboard and navigate to the **`synapseos-api`** Web Service.
2. Go to **Environment**.
3. Add the following environment variables:
   - `CLERK_SECRET_KEY`: `sk_live_...` (or `sk_test_...`)
   - `CLERK_PUBLISHABLE_KEY`: `pk_live_...` (or `pk_test_...`)
   - `CLERK_JWT_KEY`: (Your Clerk PEM public key)
   - `CLERK_ISSUER`: `https://your-app-id.clerk.accounts.dev`
4. Click **Save Changes**. Render will automatically redeploy the service.

---

## 6. Identity Mapping & Account Safety Guarantees

SynapseOS strictly prevents account hijacking and enforces data privacy:
1. **Stable External Key:** `User.clerk_user_id` stores Clerk's immutable `user_...` ID.
2. **Never Automatically Merged by Email:** If a Clerk session has an email address matching an existing pre-Clerk local account, SynapseOS **never** silently links or overwrites that account. A unique namespace is provisioned to prevent workspace takeover.
3. **Idempotent First-Login Provisioning:** When a user logs in via Clerk for the first time:
   - A new internal `User` record with a unique UUID is created.
   - An isolated personal `Workspace` is created.
   - A `WorkspaceMember` record with role `OWNER` is created.
4. **Tenant Isolation:** All downstream database tables (`memories`, `documents`, `projects`, `approval_sessions`) reference internal `Workspace.id` and `User.id` UUIDs. A Clerk user can only ever access their own authorized workspace resources.

---

## 7. Verification Checklist

Run the automated test suites locally:

```bash
# 1. Clerk Backend Authentication Suite (8 tests)
pytest apps/api/tests/test_clerk_auth.py -v

# 2. Complete Backend Test Suite (99 tests)
pytest apps/api/tests -q

# 3. End-to-End Acceptance Suite (8 steps)
python scripts/e2e_acceptance_test.py

# 4. RAG & Agent Safety Benchmark (52 queries)
python scripts/evaluate_rag_agent.py

# 5. Frontend Typecheck & Next.js Static Build
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
```

---

## 8. Troubleshooting & Rollback

- **Symptom: 401 "Invalid Clerk token signature"**:
  - Verify that `CLERK_JWT_KEY` matches the public key in your Clerk Dashboard under **API Keys > JWT Public Key**.
  - Ensure the issuer URL matches `CLERK_ISSUER`.
- **Symptom: Middleware redirect loop**:
  - Verify that public routes (`/`, `/login`, `/register`, `/api(.*)`) are excluded in `apps/web/src/middleware.ts`.
- **Rollback Procedure**:
  - If Clerk needs to be disabled temporarily:
    - Simply remove or unset `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` in Vercel and `CLERK_JWT_KEY` in Render.
    - SynapseOS automatically falls back to local authentication mode with zero code edits.
