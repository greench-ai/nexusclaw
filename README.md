# NexusClaw

**Your framework. Your rules. No restrictions.**

> Freedom-first unified AI agent framework. No locked features, no forced workflow, no correct way to use it. You define everything.

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

## Why NexusClaw?

| Platform | Philosophy |
|----------|-----------|
| **Claude/GPT** | Use it our way. Pay us. |
| **OpenAI Agents** | Use it our way. Pay us. |
| **LangChain** | Write boilerplate forever. |
| **OpenClaw** | Use any model, any channel, your rules. |
| **NexusClaw** | OpenClaw + EvoClaw + Perplexity + AnythingLLM + OpenWebUI + OpenRoom = **You** |

NexusClaw is OpenClaw's philosophy (user owns everything, local + cloud, no restrictions) with the features of every major AI platform combined into one coherent framework.

---

## Features

### 🤖 Providers (No Lock-in)
- **Local**: Ollama (free, private, GPU optional)
- **OpenAI**: GPT-4o, o1, o3, o1-mini
- **Anthropic**: Claude 3.5 Sonnet, 3.5 Haiku
- **Minimaxi**: M2.7-highspeed (fast + cheap)
- **OpenRouter**: 100+ models via single API
- **Custom**: Any OpenAI-compatible endpoint

### 💬 Channels
| Channel | Status |
|---------|--------|
| Web UI (OpenRoom) | ✅ Built |
| CLI/Terminal | ✅ Built |
| Telegram Bot | ✅ Built |
| Discord Bot | ✅ Built |
| Slack | 🏗️ Planned |

### 🧠 Memory
| Type | Status |
|------|--------|
| Persistent (Qdrant vector DB) | ✅ Built |
| Session only | ✅ Built |
| Hybrid | ✅ Built |
| RAG over documents | ✅ Built |

### 🌀 Self-Evolution (EvoClaw)
- Heartbeat every 5 minutes
- Reflection on pivotal experiences
- Research cycle (30-min keyword research)
- RSS passive information stream
- Brain organs: Consolidation, Anchor Audit, Curiosity Tracker

### 🔍 Tools
| Tool | Status |
|------|--------|
| Perplexity-style web search | ✅ Built |
| Code execution sandbox | ✅ Built |
| File operations | ✅ Built |
| Document Q&A (RAG) | ✅ Built |
| Autonomous goals | ✅ Built |
| Kill switch | ✅ Built |

### 🎭 Soul System
- Blank, Assistant, Coder, Researcher templates
- Write your own identity
- Interactive soul editor
- Hot-swap souls mid-conversation

### 🛡️ Safety
- Autonomous goals with task planning
- Approval workflow for sensitive actions
- Kill switch to pause all active goals
- Tool permission system (public/trusted/private/blocked)

### 🔌 Plugin System
- Hook-based architecture (like OpenClaw)
- Templates for: channel, provider, tool, memory, theme
- Easy plugin creation

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw

# 2. Setup (one-time wizard)
python3 src/onboard/setup.py

# 3. Start API
python3 apps/api/main.py

# 4. Open web UI
python3 apps/web/server.py
# Then open http://localhost:51234

# Or use Docker
docker-compose up
```

### CLI Usage

```bash
nexusclaw setup              # First-time configuration
nexusclaw chat               # Interactive chat
nexusclaw chat --provider openai --model gpt-4o
nexusclaw soul --edit        # Edit soul interactively
nexusclaw tools              # List all tools
nexusclaw memory "search query"  # Query memory
nexusclaw kb add --file mydoc.pdf
nexusclaw status             # System status
```

---

## Architecture

```
nexusclaw/
├── apps/
│   ├── api/                # FastAPI: auth, chat, files, autonomy
│   ├── worker/             # File indexer: PDF, DOCX, HTML, TXT
│   ├── model-gateway/      # Unified streaming for all providers
│   ├── web/                # OpenRoom browser UI
│   │   ├── index.html      # Full-featured chat interface
│   │   └── server.py       # WebSocket proxy server
│   ├── channels/
│   │   ├── telegram/       # Telegram bot
│   │   └── discord/        # Discord bot
│   └── ...
├── src/
│   ├── cli/                # nexusclaw command
│   ├── onboard/            # Setup wizard
│   ├── soul/               # Identity engine
│   ├── providers/          # Ollama, OpenAI, Anthropic, Minimaxi
│   ├── memory/             # Vector store + RAG
│   ├── knowledge/          # Knowledge base manager
│   ├── tools/              # Tool registry + web search
│   ├── evoclaw/            # Self-evolution engine
│   ├── autonomy/            # Goal execution + approval gates
│   └── plugins/            # Plugin system
├── API.md                   # Full API reference
├── install.sh              # OpenClaw-style installer
├── docker-compose.yml      # Full stack deployment
└── pyproject.toml         # Python packaging
```

---

## Version History

| Version | Key Features |
|---------|-------------|
| v0.1 | Framework skeleton, onboarding wizard |
| v0.5 | EvoClaw self-evolution engine |
| v0.6 | OpenRoom web UI + API |
| v0.7 | Telegram + Discord channels |
| v0.8 | Qdrant vector memory |
| v0.9 | Autonomy executor + kill switch |
| v0.10 | RAG pipeline |
| v0.11 | Perplexity-style web search |
| v0.12 | OpenClaw-style installer |
| v0.15 | Full setup wizard |
| v0.16 | Knowledge base manager |
| v0.17 | Plugin system |
| v0.18 | Tool registry + permissions |
| v0.19 | Soul editor |
| v0.20 | API documentation |
| v0.21 | Complete CLI |

---

## Design Documents

21 design iterations in `/home/greench/New Proj/`:
- `1st` — Product definition (4 pillars)
- `5th` — GitHub setup + .gitignore
- `10th` — v0.6: Parsers + retry queue + provider-fallback streaming
- `15th` — v0.8: Prisma models (AutonomousGoal, Task, Event, ApprovalRequest, Policy)
- `20th` — Continuity checklist: Phase A-E
- `21st` — One-shot QA pack

---

## License

MIT — Fork it. Modify it. Make it yours.

---

*Built with freedom by Greench + Naruto*
