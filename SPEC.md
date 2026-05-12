# NexusClaw — Specification

**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** v1 core done, RAG added, v2 features in progress

---

## What is NexusClaw?

Self-hosted AI gateway and agent platform. No LiteLLM. No vendor lock-in.

```
Browser → NexusClaw API → Provider API (OpenAI-compatible)
              ↓
         ~/.nexusclaw/config.yaml
```

---

## v1 — What it is (CURRENT)

### ✅ Core features deployed
- Model switching (all providers, all models, instantly)
- WebSocket streaming chat
- Settings page (add/switch/delete providers, set default model, api_mode)
- CLI onboard wizard (30+ providers, security warning, QuickStart mode)
- Docker Compose deployment
- Conversation history (SQLite — create/switch/delete, auto-save on message)

### ✅ Views (9 total)
| Route | View | Description |
|---|---|---|
| `/chat` | ChatView | Chat + model selector + conversation sidebar |
| `/brain` | BrainView | Digital Brain — Mem0 proxy at host.docker.internal:8765 |
| `/rag` | RAGView | Document upload, semantic search, chat with context |
| `/skills` | SkillsView | Marketplace (install from URL) + proposal workflow |
| `/manager` | ManagerView | Agent sessions dashboard |
| `/collections` | CollectionsView | Qdrant collection explorer |
| `/group-chat` | GroupChatView | Multi-agent UI (agent picker, team type, task runner) |
| `/browser` | BrowserView | Playwright browser control (sessions, navigate, screenshot) |
| `/settings` | SettingsView | Provider management + api_mode display |

### ✅ API endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/config` | All providers + default model + api_mode |
| POST | `/api/v1/config/provider` | Add/update provider (merges with existing) |
| DELETE | `/api/v1/config/provider/{name}` | Remove provider |
| POST | `/api/v1/chat` | Non-streaming chat |
| WS | `/api/v1/stream/{workspace_id}` | Streaming chat + auto-saves to SQLite |
| GET | `/api/v1/conversations` | List all conversations |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations/{id}` | Get conversation |
| GET | `/api/v1/conversations/{id}/messages` | Get messages |
| POST | `/api/v1/conversations/{id}/messages` | Add message |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |
| GET | `/api/v1/brain/stats` | Mem0 health + memory count |
| POST | `/api/v1/brain/search` | Semantic search in memories |
| GET | `/api/v1/brain/memories` | All memories |
| POST | `/api/v1/brain/memories` | Add memory |
| DELETE | `/api/v1/brain/memories/{id}` | Delete memory |
| POST | `/api/v1/rag/upload` | Upload document → parse → chunk → embed → store |
| GET | `/api/v1/rag/documents` | List indexed documents |
| DELETE | `/api/v1/rag/documents/{doc_id}` | Delete document + chunks |
| POST | `/api/v1/rag/search` | Semantic search across documents |
| POST | `/api/v1/rag/chat` | Chat with RAG context |
| GET | `/api/v1/skills/marketplace` | List installed skills |
| POST | `/api/v1/skills/marketplace/install` | Install skill from URL |
| DELETE | `/api/v1/skills/marketplace/{name}` | Uninstall skill |
| GET | `/api/v1/skills/proposals` | List proposals |
| POST | `/api/v1/skills/proposals` | Submit proposal |
| POST | `/api/v1/skills/proposals/{id}/approve` | Approve → writes SKILL.md |
| POST | `/api/v1/skills/proposals/{id}/reject` | Reject proposal |

### Supported providers
Ollama, OpenRouter, DeepSeek, Groq, DashScope, OpenAI, Anthropic, MiniMax, Custom Provider (any OpenAI-compatible API).

### Docker networking
- `OLLAMA_URL=http://172.29.192.1:11434` (WSL2 Ollama for RAG embeddings)
- `host.docker.internal:host-gateway` (Windows host from Docker)
- Qdrant at `qdrant-nexusclaw:6333` (nexusclaw_default Docker network)
- Mem0 at `host.docker.internal:8765` (Digital Brain on Windows)

### Known issues
- No Rerank endpoint yet (colbert/rerankers not integrated)
- GroupChat/Manager/Browser — UI present but backend endpoints for actual execution not connected
- Skills marketplace — skill execution not wired to agent runtime
- Collections view — Qdrant must be running (`docker run -d --name qdrant-nexusclaw -p 6333:6333 qdrant/qdrant:latest` then `docker network connect nexusclaw_default qdrant-nexusclaw`)

---

## v2 — What we're building

### Planned features
- **RAG增强**: Reranking (colbert), citation fact-check endpoint, focus modes (copilot/academic/writing)
- **Discord bot**: WebSocket bridge to NexusClaw `/chat/stream`
- **Telegram bot**: Long polling bridge to NexusClaw
- **MCP tool execution**: Connect MCP servers, call tools from agents
- **Agent runtime**: Tool execution, browser automation, file system tools
- **Prompt templates**: SQLite CRUD + interpolation in chat
- **Conversation title**: Auto-generate from first message

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
| Orange | `#ff6b35` |

**Fonts:** Space Grotesk (body) + IBM Plex Mono (code/mono)  
**Effects:** Glow shadows, grain noise overlay, custom scrollbar, `translateY` hover lifts

---

## Deployment

```bash
# One-line install
curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash

# Manual
git clone https://github.com/greench-ai/nexusclaw.git
cd nexusclaw && docker-compose up -d
open http://localhost:14300/setup

# Start Qdrant (needed for RAG + Collections)
docker run -d --name qdrant-nexusclaw -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
docker network connect nexusclaw_default qdrant-nexusclaw
```

---

## Config (`~/.nexusclaw/config.yaml`)

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
