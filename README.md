# NexusClaw

**Your framework. Your rules. No restrictions.**

A unified AI agent framework combining the best of OpenClaw, EvoClaw, Claude, Perplexity, AnythingLLM, OpenWebUI, OpenRoom, and Space Agent — into one freedom-first platform.

> Public version. GreenchClaw = private variant with personal customizations.

---

## Features

### 🤖 Providers (No Lock-in)
- **Local**: Ollama (free, private, runs on any machine)
- **Cloud**: OpenAI GPT-4o/o1/o3, Anthropic Claude 3.5/3.7, Minimaxi M2.7-highspeed
- **Aggregator**: OpenRouter (100+ models via single API)
- **Custom**: Any OpenAI-compatible endpoint

### 💬 Channels
- **Web**: OpenRoom browser UI (streaming, code highlighting, math rendering, voice input)
- **CLI**: Terminal/SSH
- **Telegram**: Chat from anywhere
- **Discord**: Server/community bot
- **Slack**: Team workspace

### 🧠 Memory
- **Persistent**: Qdrant vector DB — learns forever across sessions
- **Session**: Zero persistence — maximum privacy
- **Hybrid**: Remember important, forget rest

### 🌀 Self-Evolution (EvoClaw)
- Heartbeat every 5 minutes
- Reflection on pivotal experiences
- Research cycle (30-min keyword research)
- RSS passive information stream

### 🔍 Tools
- **Web Search**: Perplexity-style with citations
- **Code Execution**: Python/JS in sandbox
- **File Ops**: Read, write, browse filesystem
- **RAG**: Document Q&A over your files (PDF, DOCX, TXT, HTML)
- **API**: Call any external API

### 🎭 Soul System
- Blank, Assistant, Coder, Researcher templates
- Write your own identity
- Hot-swap souls mid-conversation

### 🛡️ Safety (Autonomy)
- Autonomous goals with task planning
- Approval workflow for sensitive actions
- Kill switch to pause all active goals

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw

# 2. Setup (one-time wizard)
python3 src/onboard/wizard.py

# 3. Start API
python3 apps/api/main.py

# 4. Open web UI
open apps/web/index.html

# Or use CLI
python3 src/cli/main.py chat
```

---

## Architecture

```
nexusclaw/
├── src/
│   ├── cli/           # nexusclaw setup / chat / shell
│   ├── onboard/       # OpenClaw-style setup wizard
│   ├── soul/         # Identity engine (user-defined personality)
│   ├── providers/    # Ollama, OpenAI, Anthropic, Minimaxi, Custom
│   └── web/          # OpenRoom UI module
├── apps/
│   ├── api/          # FastAPI: auth, chat, files, goals, kill switch
│   ├── worker/       # File indexer: PDF, DOCX, HTML, TXT → chunks → Qdrant
│   ├── model-gateway/ # Unified streaming gateway for all providers
│   └── web/          # OpenRoom browser UI
└── packages/          # Shared libraries
```

---

## License

MIT
