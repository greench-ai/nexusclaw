# NexusClaw 🤖⚡

> **Your framework. Your rules.**

NexusClaw is a self-hostable AI agent framework that combines the best ideas from Claude, EvoClaw, AnythingLLM, OpenWebUI, Perplexity, Antigravity, and Space Agent — with an OpenRoom-inspired UI.

No lock-in. No subscriptions. Your data, your infrastructure.

---

## ⚡ One-Line Install

```bash
curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash
```

Or on Windows:
```powershell
irm https://github.com/greench-ai/nexusclaw/raw/main/install.ps1 | iex
```

Or with Docker:
```bash
git clone https://github.com/greench-ai/nexusclaw.git && cd nexusclaw && docker-compose up
```

---

## ✨ Features

### 🤖 AI & Agents
- **Multi-provider**: OpenAI, Anthropic, Ollama, OpenRouter, Perplexity — all in one
- **Multi-agent orchestration**: CEO-style task delegation to specialized agents
- **Autonomous goals**: Set objectives, approve plans, let it execute
- **Tool use**: Web search, code execution, file ops, browser control

### 🧠 Memory & Knowledge
- **Vector RAG**: Qdrant/ChromaDB/LanceDB for long-term knowledge
- **Session memory**: Full conversation context per session
- **Document ingestion**: PDF, DOCX, TXT, HTML, MD → searchable knowledge
- **EvoClaw self-evolution**: Reflects on experiences, updates beliefs

### 🎭 Soul System
- **Hot-swappable personalities**: Assistant, Coder, Researcher, DevOps
- **Identity editor**: Customize your AI's character and principles
- **Template library**: Start from proven templates

### 🛠️ Skills & Workflows
- **20+ built-in skills**: Web search, security audit, morning briefing, self-improvement, and more
- **SKILL.md format**: OpenWebUI-compatible skill definitions
- **Workflow engine**: Multi-step automation pipelines
- **Skill marketplace**: Install skills from GitHub

### 💬 Interface
- **OpenRoom-inspired web UI**: Dark, minimal, modern
- **WebSocket streaming**: Real-time responses
- **REST API**: Integrate with anything
- **CLI**: Full command-line control
- **Channels**: Telegram + Discord bots

---

## 🚀 Quick Start

```bash
# 1. Install (one line)
curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash

# 2. Configure (first time only)
nexusclaw setup

# 3. Start chatting
nexusclaw chat

# Or open the web UI
open http://localhost:19789
```

---

## 📦 What's Included

| Component | Description |
|-----------|-------------|
| `install.sh` | One-line installer (Linux/macOS/WSL) |
| `install.ps1` | Windows installer |
| `docker-compose.yml` | Zero-dependency Docker setup |
| `apps/api/` | FastAPI REST + WebSocket API server |
| `apps/web/` | OpenRoom-inspired web UI |
| `apps/channels/` | Telegram + Discord bot bridges |
| `src/providers/` | Unified multi-provider LLM gateway |
| `src/memory/` | Vector RAG + session memory |
| `src/soul/` | Soul/personality engine |
| `src/tools/` | Tool registry (search, code, browser) |
| `src/evoclaw/` | Self-evolution (heartbeat, reflection, research) |
| `src/autonomy/` | Goal planning + execution engine |
| `src/skills/` | Skill system + marketplace |
| `src/workflows/` | Workflow automation engine |
| `src/agents/` | Multi-agent orchestration |
| `skills/` | 20+ built-in skills |
| `docs/blueprint/` | Full build blueprint |

---

## 🔧 Manual Install

```bash
git clone https://github.com/greench-ai/nexusclaw.git ~/nexusclaw
cd ~/nexusclaw
pip install -r requirements.txt
python src/onboard/setup.py    # First-time wizard
python apps/api/main.py         # Start API (port 8080)
python apps/web/server.py        # Start Web UI (port 19789)
```

---

## 🐳 Docker

```bash
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw
cp .env.example .env  # Add your API keys
docker-compose up
# → API: http://localhost:8080
# → Web: http://localhost:19789
```

---

## 🖥️ CLI Reference

```bash
nexusclaw setup              # Configure (first time)
nexusclaw chat               # Interactive chat
nexusclaw chat --model gpt-4o --provider openai
nexusclaw status             # System health
nexusclaw doctor             # Diagnose issues
nexusclaw soul --list        # List souls
nexusclaw soul --edit        # Edit soul
nexusclaw skills list        # List skills
nexusclaw skills run <name>  # Run a skill
nexusclaw memory "query"     # Query long-term memory
nexusclaw kb add --file x.pdf # Add to knowledge base
nexusclaw autonomy goals     # View goals
nexusclaw autonomy kill      # Kill all goals
nexusclaw update             # Update from GitHub
```

---

## 🌐 Supported Providers

| Provider | API Key Required | Local |
|----------|-----------------|-------|
| OpenRouter | ✅ | ❌ |
| OpenAI | ✅ | ❌ |
| Anthropic | ✅ | ❌ |
| Perplexity | ✅ | ❌ |
| Ollama | ❌ | ✅ |
| LM Studio | ❌ | ✅ |
| vLLM | ❌ | ✅ |

---

## 🏗️ Architecture

```
nexusclaw/
├── apps/
│   ├── api/          # FastAPI REST + WebSocket
│   ├── web/          # Web UI (OpenRoom-style)
│   ├── channels/     # Telegram + Discord
│   └── model-gateway/  # Unified streaming gateway
├── src/
│   ├── providers/   # Multi-provider LLM engine
│   ├── memory/       # Vector + session memory
│   ├── soul/        # Personality engine
│   ├── tools/       # Tool registry + execution
│   ├── evoclaw/     # Self-evolution engine
│   ├── autonomy/    # Goal planning + execution
│   ├── skills/      # Skill system
│   ├── workflows/   # Workflow automation
│   └── agents/      # Multi-agent system
├── skills/          # Built-in skills
└── docs/
    └── blueprint/   # Full build blueprint
```

---

## 📄 License

MIT — Use it, modify it, sell it, fork it. Your framework. Your rules.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Submit a PR

Issues, feature requests, and contributions welcome.
