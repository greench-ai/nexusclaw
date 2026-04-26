# NexusClaw — Personal AI Gateway

> Built on [OpenClaw](https://github.com/openclaw/openclaw) · MIT License

NexusClaw is a private, full-featured fork of OpenClaw — rebranded, extended, and packaged for personal use across any machine.

---

## What's Different from OpenClaw

| Feature | OpenClaw | NexusClaw |
|---------|----------|-----------|
| EvoClaw soul evolution | Manual install | **Bundled, auto-configured** |
| EvoClaw heartbeat | Manual cron | **Every 15 min, pre-wired** |
| Memory consolidation | Not included | **Every 30 min, pre-wired** |
| Library/docs cron | Not included | **Hourly, pre-wired** |
| UI themes | 1 default | **10 themes, live switchable** |
| Claude preview panel | Not included | **Bundled** |
| Chrome extension | Not included | **Bundled** |
| Image generation skill | Not included | **ComfyUI / A1111 / Replicate** |
| Web search skill | Not included | **Bundled (Brave / DDG)** |
| Install script | `npm install -g openclaw` | **`install.sh` — one command** |

---

## Quick Start

### Native (recommended)

```bash
# Clone and install
git clone https://github.com/greench/nexusclaw.git
cd nexusclaw
bash install.sh --daemon

# Start
nexusclaw gateway
```

### One-liner (from release)

```bash
curl -sSL https://raw.githubusercontent.com/greench/nexusclaw/main/install.sh | bash
nexusclaw onboard --install-daemon
```

### Docker

```bash
cp .env.example .env
# Edit .env with your API keys
docker compose up -d
```

---

## Config

Config lives at `~/.nexusclaw/nexusclaw.json`.

```json
{
  "agent": { "model": "anthropic/claude-opus-4-6" },
  "gateway": { "port": 19789 },
  "cron": [
    { "schedule": "*/15 * * * *", "skill": "evoclaw/heartbeat" },
    { "schedule": "*/30 * * * *", "skill": "memory-save/run" },
    { "schedule": "0 * * * *",    "skill": "library-update/run" }
  ],
  "ui": { "theme": "aurora", "claudePreview": true }
}
```

Full config reference: [OpenClaw docs](https://docs.openclaw.ai/gateway/configuration) (same keys, replace `~/.openclaw` with `~/.nexusclaw`)

---

## Bundled Skills

| Skill | Trigger | What it does |
|-------|---------|-------------|
| `evoclaw` | Every 15 min | Soul evolution + memory classification |
| `memory-save` | Every 30 min | Session context consolidation |
| `library-update` | Every hour | Keeps `~/nexusclaw/library/` updated |
| `image-create` | On demand | Image generation via ComfyUI / A1111 |
| `web-search` | Auto / on demand | Real-time web search |

---

## UI Themes

Switch themes from the header or in config:

| ID | Name | Style |
|----|------|-------|
| `aurora` | Aurora | Default — green/purple/orange on dark |
| `midnight` | Midnight | Navy/cyan deep space |
| `obsidian` | Obsidian | Black/red/silver |
| `arctic` | Arctic | Light — white/ice blue |
| `ember` | Ember | Dark amber glow |
| `matrix` | Matrix | Terminal green on black |
| `sakura` | Sakura | Light — pink/rose |
| `void` | Void | Pure dark violet |
| `solar` | Solar | Light — warm gold |
| `stealth` | Stealth | Grey/charcoal minimal |

---

## Chrome Extension

Located in `extensions/chrome/`. Load as unpacked extension:

1. Open `chrome://extensions`
2. Enable Developer Mode
3. Click "Load unpacked"
4. Select `extensions/chrome/`

Keyboard shortcuts:
- `Ctrl+Shift+X` — Send selected text to agent
- `Ctrl+Shift+P` — Send current page to agent
- `Ctrl+Shift+N` — Open NexusClaw popup

---

## Library

All documentation auto-maintained at `~/nexusclaw/library/`:

```
~/nexusclaw/library/
├── README.md          ← Auto-generated index
├── system/            ← Config, skills, cron history
├── sessions/          ← Session logs by date
├── memory/            ← Persistent facts and tasks
├── agents/            ← SOUL.md copy + evolution log
└── skills/            ← Per-skill activity logs
```

---

## Rebrand from OpenClaw

See [`docs/rebrand-map.md`](docs/rebrand-map.md) for a complete file-by-file guide.

---

## Machines

This instance configured for `greench-ai` network:

- `freaked` — 192.168.178.90 (Docker, primary services)
- `Greench` — 192.168.178.76 (Win11, ComfyUI at :8188)
- `Aspire` — 192.168.178.96 (Naruto, Docker, MCP)

---

## License

MIT — same as OpenClaw upstream.
