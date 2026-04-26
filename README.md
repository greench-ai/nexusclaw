# NexusClaw

**Your framework. Your rules. No restrictions.**

NexusClaw is a unified AI agent framework that combines the best of OpenClaw, EvoClaw, Claude, Perplexity, AnythingLLM, OpenWebUI, and more — into one freedom-first platform.

## Philosophy

- **No agents by default** — You configure what you need during onboarding
- **No restrictions** — Local models OR cloud APIs, your choice  
- **Your data, your rules** — Privacy-first, runs wherever you want
- **Open source** — MIT license, fork and modify freely

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | bash

# Setup (one-time wizard)
nexusclaw setup

# Start chatting
nexusclaw chat
```

## Architecture

- `src/onboard/` — Setup wizard (OpenClaw-style, user defines everything)
- `src/soul/` — Identity engine (user-defined personality and rules)
- `src/providers/` — Multi-provider support (Ollama, OpenAI, Anthropic, Minimaxi, Custom)
- `src/channels/` — Communication channels (CLI, Telegram, Discord, etc.)
- `src/memory/` — Memory systems (persistent, session, hybrid)
- `src/tools/` — Tool framework (extensible, no restrictions)

## License

MIT
