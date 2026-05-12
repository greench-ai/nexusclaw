# NexusClaw v1 — SPEC

## What it is

Self-hosted AI chat platform. You run it on your own server. Add an API key. Chat with any model.

**Architecture: NO LiteLLM.** Direct calls to provider APIs. Like OpenClaw.

## How it works

```
User browser → NexusClaw API (Python/FastAPI) → Provider API (OpenAI-compatible)
                                       ↑
                               Config: ~/.nexusclaw/config.yaml
```

Providers supported (OpenAI-compatible API format):
- **Ollama** — local models, no API key needed
- **OpenRouter** — 100+ models via single key
- **DeepSeek** — fast, cheap
- **Groq** — blazingly fast
- **DashScope** — Qwen models

## Model naming

`provider/model-id` — e.g. `openai/gpt-4o`, `openrouter/deepseek-chat-v3.1`, `ollama/llama3`

OpenClaw pattern: model prefix determines the provider plugin to use.

## First-run setup (`/setup`)

1. User opens `http://localhost:14300/setup`
2. Picks a provider (Ollama, OpenRouter, DeepSeek, Groq, DashScope)
3. Pastes API key (skipped for Ollama)
4. Picks or types a model
5. Clicks **Save & Chat**
6. Redirects to `/chat`

## Chat (`/chat`)

- Model selector dropdown (shows configured models)
- Message input → sends to correct provider API
- Streaming responses
- Clean, minimal UI

## Config (`~/.nexusclaw/config.yaml`)

```yaml
version: "1.0.0"
default_provider: openrouter
default_model: openrouter/deepseek-chat-v3.1
providers:
  openrouter:
    api_key: sk-or-v1-...
    base_url: https://openrouter.ai/api/v1
    models:
      - openrouter/deepseek-chat-v3.1
      - openrouter/qwen3-8b
      - openrouter/nvidia/nemotron-3-super-120b-a12b:free
  ollama:
    base_url: http://localhost:11434/v1
    models:
      - ollama/llama3
```

## API endpoints

- `GET /api/v1/config` — read config (no keys exposed)
- `POST /api/v1/config/provider` — add/update a provider
- `POST /api/v1/chat/stream` — SSE streaming chat, `model` param = `provider/model-id`
- `POST /api/v1/chat` — non-streaming chat (for testing)

## What is NOT in v1

- No RAG, no document upload
- No Discord/Telegram bots
- No MCP tools
- No multi-agent
- No skills system
- No group chat

## Success criteria

1. Fresh install → setup page works
2. User adds OpenRouter API key → model responds
3. User never touches a config file to get things working
