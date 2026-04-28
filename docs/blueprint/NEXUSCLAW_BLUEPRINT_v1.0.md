# NexusClaw — Full Build Blueprint v1.0
**Date:** 2026-04-28  
**Author:** Greench + Naruto  
**Status:** Ready to Build  
**GitHub:** https://github.com/greench-ai/nexusclaw

---

## 1. Vision

NexusClaw is the AI agent framework that should exist but doesn't: a single coherent platform that combines the best ideas from every major AI platform into one freedom-first, zero-lock-in, self-hostable system.

**Philosophy:** Your framework. Your rules. No restrictions.

**What it replaces:**
| Instead of | NexusClaw does |
|-----------|----------------|
| Claude Code (locked to Anthropic) | Any model, any provider |
| OpenWebUI (chat-first) | Chat + agents + autonomy + skills |
| AnythingLLM (RAG-only) | RAG + agents + tools + autonomy |
| Perplexity (cloud-only) | Web search + local + API |
| Antigravity (CLI-only) | CLI + Web UI + API + channels |
| Space Agent (browser-only) | Browser + filesystem + code + agents |
| OpenRoom (UI-only) | UI + brain + soul + memory + evolution |

**Installation:** `curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash` — works on Linux/macOS/WSL. One line. Done.

---

## 2. Feature Map (All Platforms → NexusClaw)

### 2.1 From OpenClaw (Framework Foundation)
- [x] Hook-based plugin architecture
- [x] Multi-provider model gateway (OpenAI, Anthropic, Ollama, OpenRouter, etc.)
- [x] Session management with context windows
- [x] Tool permission system (public/trusted/private/blocked)
- [x] CLI command structure
- [x] Gateway/daemon mode
- [x] Health checks
- [x] Workspace isolation
- [x] **MISSING:** Multi-agent orchestration (CEO → Departments)
- [x] **MISSING:** Skill marketplace (ClawHub-style)
- [x] **MISSING:** Cron job scheduler

### 2.2 From Claude (Intelligence & Reasoning)
- [x] Multi-step task planning
- [x] Tool use with error recovery
- [x] Self-correction loops
- [x] **MISSING:** Computer use / browser agent
- [x] **MISSING:** Result caching across sessions
- [x] **MISSING:** Project memory (persistent context per workspace)

### 2.3 From EvoClaw (Self-Evolution)
- [x] Heartbeat system (workspace validators, health checks)
- [x] Reflection on pivotal experiences → beliefs
- [x] Consolidation layer (experiences → beliefs over time)
- [x] Anchor audit (identity drift detection)
- [x] Curiosity tracker ("wait. what?" moments)
- [x] Research cycle (30-min keyword research)
- [x] RSS passive information stream
- [x] **MISSING:** Full EvoClaw integration (run EvoClaw from within NexusClaw)
- [x] **MISSING:** Self-improvement organ builder

### 2.4 From AnythingLLM (RAG & Knowledge)
- [x] Document ingestion (PDF, DOCX, TXT, HTML, MD)
- [x] Vector database (Qdrant — already integrated)
- [x] Workspace-based knowledge isolation
- [x] Chat with documents
- [x] Embedding models (Ollama/local)
- [x] **MISSING:** Multi-workspace management UI
- [x] **MISSING:** Citation highlighting in responses
- [x] **MISSING:** Document chunk management UI
- [x] **MISSING:** LanceDB option (in addition to Qdrant)
- [x] **MISSING:** URL scraping → knowledge base

### 2.5 From OpenWebUI (UI & Agents)
- [x] Full chat interface with streaming
- [x] WebSocket real-time updates
- [x] Model selector
- [x] Chat history / sessions
- [x] Prompt templates
- [x] **MISSING:** OpenWebUI-style skill system (SKILL.md)
- [x] **MISSING:** Agentic mode toggle
- [x] **MISSING:** Built-in tools panel
- [x] **MISSING:** Image generation integration
- [x] **MISSING:** Voice mode (TTS/STT)
- [x] **MISSING:** Admin/settings panel

### 2.6 From Perplexity (Web Search)
- [x] Web search tool (already built)
- [x] URL content fetching
- [x] Grounded responses with citations
- [x] **MISSING:** Perplexity API native integration
- [x] **MISSING:** Research mode (deep dive, multi-source)
- [x] **MISSING:** Real-time web indexing
- [x] **MISSING:** Source credibility scoring

### 2.7 From Antigravity (Workflows & Skills)
- [x] 20 skills already built
- [x] Skill registry system
- [x] **MISSING:** SKILL.md format (OpenWebUI-style)
- [x] **MISSING:** Workflow engine (multi-step automation)
- [x] **MISSING:** Skill chaining
- [x] **MISSING:** Skill marketplace CLI (`nexusclaw skills search/install`)
- [x] **MISSING:** Governance-first principles
- [x] **MISSING:** 19 specialized agents (domain-specific)
- [x] **MISSING:** 31 commands

### 2.8 From Space Agent (Browser Control)
- [x] Playwright integration (already in tools/browser.py)
- [x] Screenshot capture
- [x] **MISSING:** Space Agent-style AGENTS.md hierarchy
- [x] **MISSING:** Hosted share / cloud sharing
- [x] **MISSING:** Desktop webview integration
- [x] **MISSING:** Visual browser agent (see and interact)
- [x] **MISSING:** Browser session persistence

### 2.9 From OpenRoom (UI Design)
OpenRoom is the reference UI — dark, minimal, modern. Key UI elements:
- [x] Dark theme already built (CSS vars, `--accent: #7c3aed`)
- [x] Sidebar with chat history
- [x] WebSocket streaming
- [x] Model/provider selector
- [x] Soul selector
- [x] **MISSING:** OpenRoom.com features (need to scrape/analyze)
- [x] **MISSING:** Settings panel
- [x] **MISSING:** Admin dashboard
- [x] **MISSING:** Knowledge base manager UI
- [x] **MISSING:** Skill manager UI
- [x] **MISSING:** Theme switcher
- [x] **MISSING:** Mobile-responsive layout
- [x] **MISSING:** Notifications panel
- [x] **MISSING:** Agent status panel

---

## 3. Architecture

```
nexusclaw/
├── install.sh                    # One-line installer (Linux/macOS/WSL)
├── install.ps1                   # One-line installer (Windows)
├── docker-compose.yml            # Full stack in Docker
├── Dockerfile                    # Container build
├── pyproject.toml                # Python packaging
├── package.json                  # Node.js tools
│
├── apps/
│   ├── api/                     # FastAPI: REST + WebSocket
│   │   ├── main.py              # App entry, routes, auth
│   │   ├── auth.py              # JWT auth, user management
│   │   ├── chat.py              # Chat completions, streaming
│   │   ├── sessions.py           # Session management
│   │   ├── files.py             # File upload, RAG indexing
│   │   ├── autonomy.py           # Goal executor, approvals
│   │   ├── skills.py            # Skill registry, execution
│   │   └── memory.py            # Memory queries
│   │
│   ├── worker/                  # Background indexer
│   │   └── indexer.py          # PDF/DOCX/HTML/TXT → chunks → Qdrant
│   │
│   ├── web/                     # OpenRoom UI (the face)
│   │   ├── index.html           # Full app (single HTML for simplicity)
│   │   ├── server.py            # WebSocket + static file server
│   │   ├── dashboard.html       # Admin/overview dashboard
│   │   └── components/          # UI components
│   │
│   ├── channels/                # Messaging platforms
│   │   ├── telegram/            # Telegram bot
│   │   ├── discord/             # Discord bot
│   │   └── slack/               # Slack bot (future)
│   │
│   └── model-gateway/           # Unified streaming gateway
│       └── gateway.py           # OpenAI-compatible + Ollama + Anthropic
│
├── src/
│   ├── cli/                     # nexusclaw command
│   │   └── cli.py               # Click-based CLI
│   │
│   ├── onboard/                 # Setup wizard
│   │   └── setup.py            # Interactive first-run setup
│   │
│   ├── soul/                   # Identity engine
│   │   ├── engine.py           # Soul loader, hot-swap
│   │   └── editor.py           # Soul editor
│   │
│   ├── providers/              # Model providers
│   │   ├── engine.py           # Unified provider interface
│   │   ├── openai_.py          # OpenAI + compatible
│   │   ├── anthropic_.py        # Anthropic
│   │   ├── ollama_.py           # Ollama local
│   │   ├── openrouter_.py       # OpenRouter
│   │   ├── perplexity_.py        # Perplexity API
│   │   └── minimax_.py          # Minimax
│   │
│   ├── memory/                 # Vector + session memory
│   │   ├── vector_store.py     # Qdrant client
│   │   ├── session.py           # Short-term session memory
│   │   └── rag.py              # Retrieval-augmented generation
│   │
│   ├── tools/                  # Tool registry
│   │   ├── registry.py          # Tool definitions + permissions
│   │   ├── web_search.py        # Perplexity-style search + fetch
│   │   ├── browser.py           # Playwright browser control
│   │   ├── code_exec.py         # Sandboxed Python/shell execution
│   │   ├── file_ops.py          # Read/write files
│   │   └── machine.py           # System info, processes
│   │
│   ├── evoclaw/                # Self-evolution engine
│   │   ├── heartbeat.py         # 5-min heartbeat scheduler
│   │   ├── reflection.py         # Experience → belief consolidation
│   │   ├── anchor_audit.py      # Identity drift detection
│   │   ├── curiosity.py          # "Wait. what?" moment tracker
│   │   └── research.py           # 30-min keyword research cycle
│   │
│   ├── autonomy/               # Goal execution
│   │   ├── executor.py          # Plan + execute loops
│   │   ├── planner.py          # Task decomposition
│   │   └── approval.py          # Gate-based human approval
│   │
│   ├── skills/               # Skill system
│   │   ├── registry.py         # Skill loader (SKILL.md format)
│   │   ├── executor.py         # Skill runner
│   │   └── marketplace.py      # Skill install from GitHub
│   │
│   ├── plugins/              # Plugin system (OpenClaw-style hooks)
│   │   ├── registry.py
│   │   └── hooks.py
│   │
│   ├── workflows/            # Workflow engine (Antigravity)
│   │   ├── engine.py
│   │   └── steps.py
│   │
│   └── agents/              # Multi-agent system (CEO → Departments)
│       ├── director.py       # CEO-style task delegation
│       ├── department.py     # Specialized agent groups
│       └── message_bus.py   # Event-driven agent communication
│
├── skills/                    # Built-in skills (20 exist)
│   ├── evoclaw/              # Run EvoClaw self-evolution
│   ├── web-search/           # Deep web research
│   ├── library-update/       # Update documentation
│   ├── memory-save/          # Save to long-term memory
│   ├── morning-briefing/      # Daily news + status
│   ├── self-improving-agent/  # Meta-improvement
│   ├── agent-chronicle/       # Track agent activities
│   ├── agent-audit-trail/     # Audit log
│   ├── agent-autopilot/        # Autonomous maintenance
│   ├── active-maintenance/    # System health
│   ├── arc-security-audit/    # Security scanner
│   ├── birthday-reminder/      # Personal reminders
│   ├── frontend-design/       # UI generation
│   ├── image-create/          # Image generation
│   ├── summarize/             # Document summarization
│   ├── todo-tracker/          # Task tracking
│   ├── weather/               # Weather info
│   └── wikipedia/             # Wikipedia lookup
│
├── ui/                        # Node.js UI (future Svelte migration)
│   ├── public/
│   └── themes/
│
└── docs/
    ├── README.md
    ├── API.md
    ├── SKILLS.md              # Skill format spec
    ├── WORKFLOWS.md            # Workflow format spec
    └── blueprint/
        └── NEXUSCLAW_BLUEPRINT_v1.0.md
```

---

## 4. Installation Process

### 4.1 One-Line (Linux/macOS/WSL)
```bash
curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash
```

**What install.sh does:**
1. Detects OS (Linux/macOS/WSL/Windows)
2. Clones or updates the repo to `~/nexusclaw`
3. Installs Python deps (`pip install -r requirements.txt`)
4. Installs Playwright + Chromium (optional, for browser control)
5. Installs Node.js tools (if needed)
6. Runs onboarding wizard (`nexusclaw setup`)
7. Starts all services: API (8080), Web UI (19789)
8. Prints URLs and next steps

### 4.2 One-Line (Windows)
```powershell
irm https://github.com/greench-ai/nexusclaw/raw/main/install.ps1 | iex
```

### 4.3 Docker (Zero-dependency)
```bash
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw
docker-compose up
```

### 4.4 Manual
```bash
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw
pip install -r requirements.txt
python3 src/onboard/setup.py   # First-time wizard
python3 apps/api/main.py        # Start API
python3 apps/web/server.py       # Start UI
```

---

## 5. Onboarding Wizard

Interactive first-run setup (like OpenClaw's onboard):

```
⚡ NexusClaw Setup
=====================
1. API Keys
   - OpenAI API key (optional)
   - Anthropic API key (optional)
   - Perplexity API key (optional)
   - OpenRouter API key (optional)
   - Ollama URL (default: http://localhost:11434)

2. Model Selection
   - Primary model (recommended: qwen3.5-plus)
   - Fast model (recommended: qwen3-coder-plus)
   - Embedding model (recommended: nomic-embed-text)

3. Memory Setup
   - Vector DB: Qdrant (Docker) | LanceDB | ChromaDB
   - Qdrant URL (default: http://localhost:6333)

4. Channels
   - Telegram bot token (optional)
   - Discord bot token (optional)

5. Soul
   - Choose template: Blank | Assistant | Coder | Researcher
   - Or write your own soul

6. EvoClaw
   - Enable self-evolution? (Y/n)
   - Enable heartbeat? (Y/n)
   - Enable research cycle? (Y/n)

7. Ports
   - API port [8080]
   - Web UI port [19789]

Config saved to ~/.nexusclaw/config.json
```

---

## 6. UI Specification (OpenRoom-Inspired)

### 6.1 Layout
```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR (260px)  │  MAIN CHAT AREA                │
│                   │                                 │
│  [Logo] [⚡New]  │  ┌─────────────────────────┐   │
│                   │  │ Model: [▾] Soul: [▾] │   │
│  Search...       │  │ Tools: [✓] RAG: [▾]  │   │
│                   │  └─────────────────────────┘   │
│  ── Chats ──     │                                 │
│  > Today          │  [Chat messages with streaming]│
│    Project Alpha   │                                 │
│    BTC Research    │                                 │
│  > Yesterday       │                                 │
│    Wallet Audit    │                                 │
│  > Archive         │                                 │
│                   │                                 │
│  ── Tools ──     │  ┌─────────────────────────┐   │
│  💬 Chat          │  │ Type message...     ➤ │   │
│  📁 Files         │  └─────────────────────────┘   │
│  🧠 Memory        │                                 │
│  🎭 Soul          │  [Status: EvoClaw ● | BTC ●]  │
│  🛠️ Skills        │                                 │
│  ⚙️ Settings      │                                 │
└─────────────────────────────────────────────────────┘
```

### 6.2 Pages/Views
1. **Chat** — Main conversation interface (default)
2. **Files** — Knowledge base manager (upload, chunk, search)
3. **Memory** — Memory browser, reflection viewer, belief editor
4. **Soul** — Soul editor, template picker, personality preview
5. **Skills** — Installed skills, marketplace, skill editor
6. **Workflows** — Workflow builder, run history
7. **Agents** — Multi-agent dashboard, department manager
8. **Settings** — API keys, providers, EvoClaw config, theme

### 6.3 Dashboard (Admin)
- System health (memory, CPU, GPU)
- Active sessions count
- BTC recovery status
- EvoClaw heartbeat status
- Storage usage
- Log viewer

---

## 7. Build Priority

### Phase 1: Foundation (CRITICAL PATH — must work first)
- [ ] Clean install.sh that works on Linux/macOS/WSL/Windows
- [ ] Docker setup (docker-compose.yml)
- [ ] Onboarding wizard (src/onboard/setup.py)
- [ ] Provider engine (src/providers/engine.py) — unified interface
- [ ] API server (apps/api/main.py) — FastAPI with all routes
- [ ] Web UI (apps/web/index.html) — OpenRoom-inspired interface

### Phase 2: Core Features
- [ ] WebSocket streaming (chat with real-time output)
- [ ] Soul engine (load, save, hot-swap souls)
- [ ] Memory system (Qdrant vector store, session memory, RAG)
- [ ] Tool registry (web search, code exec, file ops)
- [ ] Autonomy executor (goal planning, approval gates, kill switch)

### Phase 3: Advanced Features
- [ ] Multi-agent system (CEO director, department agents, message bus)
- [ ] Skill system (SKILL.md format, skill registry, executor)
- [ ] Workflow engine (Antigravity-style multi-step automation)
- [ ] EvoClaw integration (heartbeat, reflection, anchor audit)
- [ ] Perplexity API integration (native, not just tool)

### Phase 4: Polish
- [ ] Skills marketplace CLI (search, install from GitHub)
- [ ] Browser agent (Space Agent-style visual browser)
- [ ] OpenRoom UI matching (dashboard, settings panel)
- [ ] Mobile-responsive layout
- [ ] Theme switcher (dark/light)

---

## 8. CLI Reference

```bash
nexusclaw setup              # First-time configuration
nexusclaw chat               # Interactive chat
nexusclaw chat --model gpt-4o --provider openai
nexusclaw soul --edit        # Edit soul interactively
nexusclaw soul --list        # List available souls
nexusclaw tools              # List all available tools
nexusclaw tools --enabled    # List enabled tools
nexusclaw skills list        # List installed skills
nexusclaw skills search <q> # Search marketplace
nexusclaw skills install <n>  # Install from GitHub
nexusclaw skills run <name>  # Execute a skill
nexusclaw memory "query"     # Query long-term memory
nexusclaw kb add --file.pdf  # Add document to knowledge base
nexusclaw kb list            # List knowledge bases
nexusclaw autonomy goals      # List active goals
nexusclaw autonomy kill       # Kill switch
nexusclaw agent --new        # Spawn new agent
nexusclaw agent list         # List running agents
nexusclaw doctor             # Diagnose system health
nexusclaw status             # System status
nexusclaw update             # Update from GitHub
nexusclaw uninstall          # Clean removal
```

---

## 9. Key Technical Decisions

### Python-first backend
Chosen over Node.js for: better AI ecosystem (PyTorch, transformers), easier LLM integrations, native async for streaming.

### Single HTML web UI
Chosen over Svelte/React for simplicity and portability. One file to serve, easy to modify, zero build step. Migrate to Svelte later if needed.

### Qdrant as primary vector DB
Already working. LanceDB as optional (for zero-setup portable mode).

### SKILL.md as skill format
OpenWebUI's SKILL.md is the emerging standard. Adopt it for ecosystem compatibility.

### JSON config files
No database required for core operation. YAML/TOML for complex configs. SQLite optional for user/session storage.

---

## 10. What's Already Built (Don't Rebuild)

- ✅ Install script (`install.sh`) — works, needs cross-platform polish
- ✅ Docker compose — works
- ✅ Onboarding wizard skeleton — works
- ✅ API server (FastAPI) — works, needs routes cleaned up
- ✅ Web UI (`index.html`) — works, needs polish
- ✅ Soul engine — works
- ✅ Tool registry — works (web search, code exec, browser, machine, file ops)
- ✅ Memory (Qdrant vector + RAG) — works
- ✅ EvoClaw heartbeat/reflection/anchor/curiosity — works
- ✅ Autonomy executor — works
- ✅ 20 skills — work
- ✅ Channels (Telegram, Discord) — basic
- ✅ Provider engine — works
- ✅ GitHub repo — exists

---

## 11. GitHub Repository Setup

Already at: `https://github.com/greench-ai/nexusclaw`

**TODO:**
- [ ] Write proper README.md (this blueprint becomes the source)
- [ ] Add LICENSE (MIT)
- [ ] Add badges (build, version, license)
- [ ] Create CHANGELOG.md
- [ ] Add CONTRIBUTING.md
- [ ] Create release workflow (GitHub Actions)
- [ ] Add issue templates

---

## 12. Start Building

Greench approves → Naruto begins with **Phase 1** in this order:

1. **`install.sh`** — make it bulletproof cross-platform
2. **`install.ps1`** — Windows support
3. **`docker-compose.yml`** — make it work out of the box
4. **`requirements.txt`** — explicit pinned dependencies
5. **`apps/api/main.py`** — clean FastAPI with all routes
6. **`apps/web/index.html`** — OpenRoom-inspired UI rewrite
7. **`src/onboard/setup.py`** — complete onboarding wizard
8. **`src/providers/engine.py`** — unified provider interface

Blueprint complete. Ready to build.
