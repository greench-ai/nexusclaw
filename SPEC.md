# NexusClaw — Specification

**Version:** 1.0  
**Date:** 2026-05-12  
**Status:** v1 deployed, v2 planning

---

## What is NexusClaw?

Self-hosted AI gateway and agent platform. No LiteLLM. No vendor lock-in. You run it, you own it.

**Stack:** Python + FastAPI + React. Direct calls to provider APIs (OpenAI-compatible).

```
User browser → NexusClaw API → Provider API
                  ↑
          ~/.nexusclaw/config.yaml
```

---

## v1 — What it is (CURRENTLY DEPLOYED)

### Core features ✓
- Model switching (all providers, all models, instantly)
- WebSocket streaming chat
- Settings page (add/switch/delete providers, set default model)
- CLI onboard wizard (30+ providers, security warning, QuickStart mode)
- Docker Compose deployment

### API endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/config` | All providers + default model |
| POST | `/api/v1/config/provider` | Add/update a provider |
| DELETE | `/api/v1/config/provider/{name}` | Remove a provider |
| POST | `/api/v1/chat` | Non-streaming chat |
| WS | `/api/v1/stream/{workspace_id}` | Streaming chat |

### Supported providers
Ollama, OpenRouter, DeepSeek, Groq, DashScope, OpenAI, Anthropic, MiniMax, Custom Provider (any OpenAI-compatible API), and 20+ more via onboard wizard.

### What's working right now
- Chat with MiniMax (`custom_api_minimax_io/MiniMax-M2.7-highspeed`)
- Chat with OpenRouter DeepSeek (`openrouter/deepseek-chat-v3.1`)
- Model selector dropdown in chat bar (shows ALL models from ALL providers)
- Settings page (add/switch/delete providers, set default model)
- `nexusclaw onboard` CLI wizard

### Known issues
- Settings page shows API mode from provider config (may need to display api_mode correctly)
- No conversation history persistence (messages lost on refresh)
- No RAG/document upload
- No Discord/Telegram bots
- No skills system
- No multi-agent

---

## v2 — What we're building (IN PROGRESS)

### Architecture
```
Browser → NexusClaw API (FastAPI)
              ↓
         Agent Runtime
              ↓
         LLM Providers (direct, no LiteLLM)
              ↓
         Memory (warm: SQLite FTS5, cold: Qdrant)
              ↓
         Tools (MCP, browser, file system)
```

### Planned features for v2

#### Provider system
- 30+ built-in providers (Ollama, OpenRouter, DeepSeek, Groq, DashScope, Anthropic, OpenAI, MiniMax, Cloudflare AI, HuggingFace, Together AI, vLLM, etc.)
- Custom Provider: any OpenAI-compatible API, auto-detect mode
- Per-provider model lists with defaults

#### Chat UI
- Model selector dropdown (all models, all providers, instant switch)
- Conversation history (persisted in SQLite)
- Streaming tokens in real-time
- Copy code blocks, export conversation

#### Agent runtime
- Tool execution (MCP servers, built-in browser/file/terminal tools)
- Session management with context windows
- Multi-step task handling

#### Memory
- Warm memory: SQLite FTS5 (full-text search, fast)
- Cold memory: Qdrant (vector similarity)
- Semantic retrieval across conversation history

#### RAG pipeline
- Document upload (PDF, TXT, MD, DOCX, HTML)
- Chunking + embedding + vector storage
- Citation with fact-check verify endpoint
- Focus modes: copilot, academic, writing

#### Multi-agent
- AutoGen-powered group chat
- Persona agents: Researcher, Coder, Writer, Critic, Analyst
- Round-robin and selector team modes

#### Channel integrations
- Discord bot (WebSocket bridge)
- Telegram bot (long polling)
- CLI chat

#### Skill marketplace
- Install skills from URL (fetches SKILL.md)
- Skill formation: propose → approve → activate
- Built-in skills + remote install

#### Observability
- Prometheus metrics endpoint
- Request/response logging

---

## Design system

| Token | Value |
|---|---|
| Background | `#0a0a0a` |
| Surface | `#111118` |
| Border | `#1e1e28` |
| Text | `#f0f0f0` |
| Text secondary | `#6b6b7b` |
| Accent | `#00ff88` |
| Accent dim | `rgba(0,255,136,0.1)` |
| Orange | `#ff6b35` |

**Fonts:** Space Grotesk (body) + IBM Plex Mono (code/mono)  
**Effects:** Glow shadows, grain noise overlay, custom scrollbar, `translateY` hover lifts

---

## File structure

```
nexusclaw/
├── nexusclaw/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, route registration
│   ├── api.py           # API endpoints (config, chat)
│   ├── config.py        # Config models + YAML load/save
│   ├── providers.py      # Direct provider API calls (no LiteLLM)
│   └── cli.py           # CLI: onboard, setup, status, start
├── web/
│   ├── src/
│   │   ├── App.tsx             # Router + navbar
│   │   ├── views/
│   │   │   ├── ChatView.tsx    # Chat + model selector
│   │   │   ├── SettingsView.tsx # Provider management
│   │   │   └── SetupView.tsx   # First-run wizard
│   │   └── styles.css
│   ├── index.html
│   └── package.json
├── Dockerfile.app
├── docker-compose.yml
├── install.sh
├── pyproject.toml
└── SPEC.md
```

---

## Deployment

```bash
# One-line install
curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash

# Or manual
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw && docker-compose up -d
open http://localhost:14300/setup
```

---

## API Configuration (`~/.nexusclaw/config.yaml`)

```yaml
version: "1.0.0"
default_provider: openrouter
default_model: openrouter/deepseek-chat-v3.1
providers:
  openrouter:
    name: openrouter
    api_key: sk-or-v1-...
    base_url: https://openrouter.ai/api/v1
    api_mode: openai-chat
    models:
      - deepseek/deepseek-chat-v3.1
      - qwen/qwen3-8b
      - nvidia/nemotron-3-super-120b-a12b:free
    enabled: true
  custom_api_minimax_io:
    name: custom_api_minimax_io
    base_url: https://api.minimax.io/anthropic
    api_mode: anthropic-chat
    api_key: sk-cp-...
    models:
      - MiniMax-M2.7-highspeed
    enabled: true
```

---

## Success criteria (v1)

1. Fresh install → `/setup` wizard → chat works
2. User adds API key → model responds (no config file editing)
3. Model switching works instantly across all providers
4. Docker Compose: `up -d` → healthy container
5. No LiteLLM dependency
