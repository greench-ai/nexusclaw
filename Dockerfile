# NexusClaw — Dockerfile
# Build: docker build -t ghcr.io/greench/nexusclaw:latest .
# Run:   docker compose up -d

FROM node:24-slim AS base
LABEL org.opencontainers.image.title="NexusClaw"
LABEL org.opencontainers.image.description="NexusClaw Personal AI Gateway"
LABEL org.opencontainers.image.source="https://github.com/greench/nexusclaw"
LABEL org.opencontainers.image.licenses="MIT"

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app

# ─── Dependencies ──────────────────────────────────────────────────────────────
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/*/package.json ./apps/
COPY packages/*/package.json ./packages/

RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

# ─── Build ─────────────────────────────────────────────────────────────────────
FROM deps AS builder
COPY . .
RUN pnpm ui:build
RUN pnpm build

# ─── Runtime ───────────────────────────────────────────────────────────────────
FROM base AS runtime

# Runtime deps only
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile --prod

# Built artifacts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/apps/ui/build ./apps/ui/build

# Bundled skills
COPY skills/ /root/.nexusclaw/workspace/skills/

# Entry point
COPY nexusclaw.mjs ./
RUN chmod +x nexusclaw.mjs

# ─── Ports & Volumes ───────────────────────────────────────────────────────────
EXPOSE 19789
VOLUME ["/root/.nexusclaw"]

# ─── Health ────────────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:19789/health || exit 1

CMD ["node", "nexusclaw.mjs", "gateway", "--port", "19789", "--bind", "0.0.0.0"]
