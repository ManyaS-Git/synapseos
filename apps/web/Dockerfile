# =============================================================================
# SynapseOS Web — Dockerfile
# =============================================================================
# This Dockerfile expects the build context to be the MONOREPO ROOT
# because it needs access to packages/ for workspace dependencies.
# Build with: docker build -f apps/web/Dockerfile .

FROM node:20-alpine AS base
RUN corepack enable

# ── Dependencies ──────────────────────────────────────────────────────────────
FROM base AS deps
WORKDIR /app

# Copy only workspace manifests for layer caching
COPY package.json package-lock.json* turbo.json ./
COPY apps/web/package.json apps/web/
COPY packages/ui/package.json packages/ui/
COPY packages/types/package.json packages/types/
COPY packages/shared/package.json packages/shared/
COPY packages/config/package.json packages/config/
COPY packages/sdk/package.json packages/sdk/

RUN npm ci

# ── Build ─────────────────────────────────────────────────────────────────────
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Ensure Next.js can find workspace packages
RUN npx turbo run build --filter=@synapseos/web

# ── Production ────────────────────────────────────────────────────────────────
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/apps/web/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
