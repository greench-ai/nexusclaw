# NexusClaw — Specification

**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** v1 complete — all core features done, v2 deferred

---

## What is NexusClaw?

Self-hosted AI gateway and agent platform. No LiteLLM. No vendor lock-in.

```
Browser → NexusClaw API → Provider API (OpenAI-compatible or Anthropic)
              ↓
         ~/.nexusclaw/config.yaml
```

---

## v1 — Current State

### ✅ Core features
- Model switching (all providers, all models, instantly)
- WebSocket streaming chat with conversation persistence (SQLite)
- Auto-generate conversation titles from first message
- Focus mode picker in chat (Copilot / Academic / Writing / Custom)
- Settings page (add/switch/delete providers, api_mode)
- Auto-detect API mode for custom providers (probes endpoint)
- CLI onboard wizard (30+ providers, security warning, QuickStart mode)
- Docker Compose deployment

### ✅ Views (10 total)
| Route | View | Description |
|---|---|---|
| `/chat` | ChatView | Chat + model selector + focus mode + conversation sidebar |
| `/brain` | BrainView | Digital Brain — Mem0 proxy at host.docker.internal:8765 |
| `/rag` | RAGView | Document upload, semantic search, chat with context |
| `/skills` | SkillsView | Marketplace (install from URL) + proposal workflow |
| `/prompts` | PromptsView | Prompt templates CRUD with {{variable}} interpolation |
| `/manager` | ManagerView | Agent sessions dashboard |
| `/collections` | CollectionsView | Qdrant collection explorer |
| `/group-chat` | GroupChatView | Multi-agent UI (agent picker, team type, task runner) |
| `/browser` | BrowserView | Playwright browser control (sessions, navigate, screenshot) |
| `/settings` | SettingsView | Provider management + auto-detect api_mode |

### ✅ API endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/config` | All providers + default model + api_mode |
| POST | `/api/v1/config/provider` | Add/update provider (merges with existing) |
| POST | `/api/v1/config/provider/detect` | Auto-detect api_mode for a base_url |
| DELETE | `/api/v1/config/provider/{name}` | Remove provider |
| GET | `/api/v1/conversations` | List all conversations |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations/{id}` | Get conversation + messages |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |
| WS | `/api/v1/stream/{workspace_id}` | Streaming chat with conversation persistence |
| POST | `/api/v1/rag/upload` | Upload + parse + embed + store document |
| POST | `/api/v1/rag/search` | Semantic search across chunks |
| POST | `/api/v1/rag/verify` | Citation fact-check (claim vs chunks) |
| GET | `/api/v1/prompts` | List prompt templates |
| POST | `/api/v1/prompts` | Create prompt template |
| GET | `/api/v1/prompts/{name}` | Get template |
| PATCH | `/api/v1/prompts/{name}` | Update template |
| DELETE | `/api/v1/prompts/{name}` | Delete template |
| GET | `/api/v1/brain/stats` | Mem0 stats (memory count, model, embedder) |
| POST | `/api/v1/brain/search` | Semantic memory search |
| GET/POST/DELETE | `/api/v1/brain/memories` | Memory CRUD |

### ✅ RAG pipeline
- Upload: PDF, DOCX, TXT, MD, HTML
- Chunking: 500 tokens, 100 token overlap
- Embedding: Ollama `nomic-embed-text:v1.5` via WSL2 (accessible from Docker at 172.29.192.1:11434)
- Storage: Qdrant at `qdrant-nexusclaw:6333` on `nexusclaw_default` network
- Search: semantic vector search with score
- Context injection: RAG context appended as system prompt in WebSocket chat
- Citation fact-check: LLM verifies claims against source chunks

### ✅ Focus modes
- **Copilot**: k=5, balanced retrieval
- **Academic**: +30% score boost for academic/arxiv docs (planned)
- **Writing**: +15% score boost for prose/writing docs (planned)
- **Custom**: use custom prompt templates

### ✅ Prompt templates
- SQLite storage at `~/.nexusclaw/prompt_templates.db`
- `{{variable}}` placeholder extraction
- `interpolate(**kwargs)` returns (system_prompt, user_prompt)
- Focus mode per template (copilot/academic/writing/custom)

---

## v2 — Planned

### High priority
- Citation fact-check UI in ChatView (wire POST /rag/verify to selected text)
- RAG reranking (ColBERT cross-encoder, increase k=20 → rerank to k=5)
- Discord/Telegram WebSocket bridge (connect bot channels to /chat/stream)
- MCP tool execution pipeline (wire MCP bridge to agent runtime)
- Skills execution (wire marketplace skills to agent runtime)

### Medium priority
- Prompt template interpolation in chat (use template variables)
- Langfuse tracing (requires ClickHouse — deferred)
- Prometheus/Grafana metrics (deferred)
- Artifact system UI (ManagerView)

### Low priority
- GroupChat execution endpoints (UI present, backend not connected)
- BrowserView execution (UI present, backend not connected)
- ManagerView execution (UI present, backend not connected)

---

## Architecture

```
nexusclaw/
├── api.py              # HTTP + WebSocket chat handler
├── providers.py        # Direct httpx calls (no LiteLLM)
├── config.py           # YAML config read/write
├── conversations.py    # SQLite conversation store
├── rag.py             # RAG pipeline (parse/chunk/embed/store/search)
├── prompts.py         # Prompt template SQLite store
├── main.py            # FastAPI app + CORS + routes
├── api_*.py           # API route modules
└── cli.py             # CLI commands (onboard, discord, telegram)
```

**Config:** `~/.nexusclaw/config.yaml`
**DB:** `~/.nexusclaw/conversations.db`, `~/.nexusclaw/prompt_templates.db`
**Ports:** API 8000, Web 3000 (Docker Compose)

---

## Providers (configured)
- `MiniMax-M2.7-highspeed` — MiniMax via OpenWebUI (api_mode: anthropic-chat)
- `openrouter` — OpenRouter (api_mode: openai-chat)
- Custom providers supported via auto-detect or manual api_mode

## Key files
- `docker-compose.yml` — Full stack: nexusclaw + qdrant
- `Dockerfile.app` — NexusClaw API + Web UI
- `install.sh` — `curl | bash` installer
