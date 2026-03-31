# NexusClaw — Rebrand Map
> Every file and string to change when forking OpenClaw → NexusClaw

---

## 1. Binary & Package Identity

| File | Key | Old Value | New Value |
|------|-----|-----------|-----------|
| `package.json` | `name` | `openclaw` | `nexusclaw` |
| `package.json` | `bin.openclaw` | `./dist/cli.js` | rename key to `nexusclaw` |
| `package.json` | `description` | `Your own personal AI...` | `NexusClaw — Personal AI Gateway` |
| `pyproject.toml` | `name` | `openclaw` | `nexusclaw` |
| `openclaw.mjs` | filename | `openclaw.mjs` | `nexusclaw.mjs` |
| `openclaw.podman.env` | filename | `openclaw.podman.env` | `nexusclaw.podman.env` |

---

## 2. Source Code — String Replacements

Run these as global find-and-replace across `src/`, `apps/`, `packages/`:

```bash
# Exact replacements (case-sensitive)
OpenClaw    → NexusClaw
openclaw    → nexusclaw
OPENCLAW    → NEXUSCLAW
open-claw   → nexus-claw
openclaw.ai → nexusclaw.local   # or your domain
clawhub.com → (remove or replace with your own registry)
```

### Critical files to touch manually:

| File | What to change |
|------|---------------|
| `src/lib/constants.ts` or equivalent | APP_NAME, VERSION, all brand strings |
| `apps/gateway/src/config.ts` | Default config path `~/.openclaw` → `~/.nexusclaw` |
| `apps/gateway/src/daemon.ts` | Service name: `openclaw-gateway` → `nexusclaw-gateway` |
| `apps/ui/src/app.html` | `<title>OpenClaw</title>` → `<title>NexusClaw</title>` |
| `apps/ui/src/lib/components/Logo.svelte` | Swap in NexusClaw SVG logo |
| `scripts/*.sh` | All references to `openclaw` binary/paths |
| `docker-setup.sh` | Container names, volume names |
| `docker-compose.yml` | Service name, image name, volume names |
| `Dockerfile` | `LABEL`, binary name |
| `README.md` | Full rebrand |
| `CHANGELOG.md` | Project name |
| `VISION.md` | Project name |
| `AGENTS.md` | Project name, default persona |

---

## 3. Config & Data Paths

| Old Path | New Path |
|----------|----------|
| `~/.openclaw/` | `~/.nexusclaw/` |
| `~/.openclaw/openclaw.json` | `~/.nexusclaw/nexusclaw.json` |
| `~/.openclaw/workspace/` | `~/.nexusclaw/workspace/` |
| `~/.openclaw/credentials/` | `~/.nexusclaw/credentials/` |
| `~/.openclaw/logs/` | `~/.nexusclaw/logs/` |

---

## 4. Systemd / Launchd Service Names

| Old | New |
|-----|-----|
| `openclaw-gateway.service` | `nexusclaw-gateway.service` |
| `ai.openclaw.gateway.plist` | `dev.nexusclaw.gateway.plist` |
| Service display name: `OpenClaw Gateway` | `NexusClaw Gateway` |

---

## 5. Assets to Replace

| File | Action |
|------|--------|
| `assets/openclaw-logo.svg` | Replace with NexusClaw logo |
| `assets/openclaw-logo-text.svg` | Replace with NexusClaw logo+text |
| `apps/ui/static/favicon.png` | Replace with NexusClaw favicon |
| `apps/ui/static/icon-*.png` | Replace all icon sizes |
| `docs/assets/` | Replace all doc images |

---

## 6. Gateway WebSocket Identifier

In gateway config and handshake, the WS protocol identifier may include `openclaw`:

```typescript
// Change:
const WS_PROTOCOL = 'openclaw-gateway-v1'
// To:
const WS_PROTOCOL = 'nexusclaw-gateway-v1'
```

---

## 7. Environment Variables

| Old | New |
|-----|-----|
| `OPENCLAW_*` | `NEXUSCLAW_*` |
| `OPENCLAW_CONFIG` | `NEXUSCLAW_CONFIG` |
| `OPENCLAW_WORKSPACE` | `NEXUSCLAW_WORKSPACE` |

---

## 8. NPM / PNPM Workspace

`pnpm-workspace.yaml` — no name changes needed, but verify no hardcoded `openclaw` package refs in workspace deps.

---

## 9. GitHub Actions

`.github/workflows/ci.yml` and `release.yml`:
- Update image names: `ghcr.io/openclaw/openclaw` → `ghcr.io/greench/nexusclaw`
- Update release artifact names
- Update npm publish name if applicable

---

## 10. Post-Rebrand Verification

```bash
# Run after all replacements — should return 0 results
grep -r "OpenClaw\|openclaw\|OPENCLAW" src/ apps/ packages/ scripts/ \
  --include="*.ts" --include="*.js" --include="*.svelte" --include="*.html" \
  --include="*.json" --include="*.sh" \
  | grep -v node_modules | grep -v .git
```
