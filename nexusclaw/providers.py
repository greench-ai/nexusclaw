"""
Direct provider API calls — no LiteLLM.
Supports OpenAI Chat Completions and Anthropic Messages APIs.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from nexusclaw.config import NexusClawConfig, ProviderConfig

log = logging.getLogger(__name__)

# ── Provider defaults ─────────────────────────────────────────────────────────────

DEFAULT_BASES = {
    "openai":     "https://api.openai.com/v1",
    "anthropic":  "https://api.anthropic.com/v1",
    "ollama":     "http://localhost:11434/v1",
    "deepseek":   "https://api.deepseek.com/v1",
    "groq":       "https://api.groq.com/openai/v1",
    "dashscope":  "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def _base_url_for(provider: ProviderConfig, model: str) -> str:
    if provider.base_url:
        return provider.base_url.rstrip("/")
    prefix = model.split("/")[0] if "/" in model else provider.name
    return DEFAULT_BASES.get(prefix, "https://api.openai.com/v1")


def _auth_for(provider: ProviderConfig) -> dict[str, str]:
    if not provider.api_key:
        return {}
    # Anthropic uses x-api-key header
    if provider.api_mode == "anthropic-chat":
        return {"x-api-key": provider.api_key}
    return {"Authorization": f"Bearer {provider.api_key}"}


# ── OpenAI Chat Completions ─────────────────────────────────────────────────────

async def _openai_stream(
    url: str,
    headers: dict,
    payload: dict,
) -> AsyncIterator[dict]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code != 200:
                text = await resp.aread()
                yield {"type": "error", "error": f"HTTP {resp.status_code}: {text[:200]}"}
                return

            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    data = json.loads(line)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if content := delta.get("content"):
                        yield {"type": "token", "content": content}
                    if data.get("choices", [{}])[0].get("finish_reason") in ("stop", "length"):
                        break
                except json.JSONDecodeError:
                    pass


# ── Anthropic Messages API ───────────────────────────────────────────────────────

async def _anthropic_stream(
    url: str,
    headers: dict,
    payload: dict,
) -> AsyncIterator[dict]:
    # Convert OpenAI-style messages to Anthropic format
    anthropic_messages = []
    for msg in payload.get("messages", []):
        role = msg["role"]
        if role == "system":
            # Prepend system to first user message
            continue
        anthropic_messages.append({
            "role": "user" if role == "user" else "assistant",
            "content": msg["content"],
        })

    anthropic_payload = {
        "model": payload["model"],
        "messages": anthropic_messages,
        "stream": True,
        "max_tokens": 4096,
    }
    if payload.get("system"):
        # Put system in first user message
        if anthropic_messages and anthropic_messages[0]["role"] == "user":
            anthropic_messages[0]["content"] = f"{payload['system']}\n\n{anthropic_messages[0]['content']}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, headers=headers, json=anthropic_payload) as resp:
            if resp.status_code != 200:
                text = await resp.aread()
                yield {"type": "error", "error": f"HTTP {resp.status_code}: {text[:200]}"}
                return

            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    data = json.loads(line)
                    delta = data.get("delta", {})
                    if content := delta.get("text"):
                        yield {"type": "token", "content": content}
                    if data.get("type") == "message_stop":
                        break
                except json.JSONDecodeError:
                    pass


# ── Public API ───────────────────────────────────────────────────────────────────

async def stream_chat(
    config: NexusClawConfig,
    model: str,
    messages: list[dict],
) -> AsyncIterator[dict]:
    """
    Stream chat completion from the appropriate provider.
    Yields dicts: {"type": "token", "content": "..."} or {"type": "error", "error": "..."}
    """
    # Resolve provider
    prefix = model.split("/")[0] if "/" in model else model
    provider = config.providers.get(prefix) or config.providers.get(config.default_provider)

    if not provider:
        yield {"type": "error", "error": f"No provider for model '{model}' — run 'nexusclaw onboard' first"}
        return

    base_url = _base_url_for(provider, model)
    auth = _auth_for(provider)
    actual_model = model.split("/")[-1] if "/" in model else model

    if provider.api_mode == "anthropic-chat":
        url = f"{base_url}/v1/messages"
        headers = {**auth, "Content-Type": "application/json",
                   "anthropic-version": "2023-06-01",
                   "anthropic-dangerous-direct-browser-access": "true"}
        payload = {"model": actual_model, "messages": messages, "stream": True}
        async for chunk in _anthropic_stream(url, headers, payload):
            yield chunk

    else:
        # Default: OpenAI Chat Completions
        url = f"{base_url}/chat/completions"
        headers = {**auth, "Content-Type": "application/json"}
        payload = {"model": actual_model, "messages": messages, "stream": True}
        async for chunk in _openai_stream(url, headers, payload):
            yield chunk


async def chat(
    config: NexusClawConfig,
    model: str,
    messages: list[dict],
) -> dict:
    """Non-streaming chat — returns full response."""
    content = []
    async for chunk in stream_chat(config, model, messages):
        if chunk["type"] == "token":
            content.append(chunk["content"])
        elif chunk["type"] == "error":
            return {"error": chunk["error"]}
    return {"content": "".join(content), "model": model}
