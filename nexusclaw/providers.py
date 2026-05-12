"""
Direct provider API calls — no LiteLLM.
Each provider uses OpenAI-compatible chat completions API.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from nexusclaw.config import NexusClawConfig, ProviderConfig

log = logging.getLogger(__name__)


def _get_auth_header(provider: ProviderConfig, model: str) -> dict[str, str]:
    """Build auth headers for a provider."""
    prefix = model.split("/")[0] if "/" in model else model

    if provider.api_key:
        return {"Authorization": f"Bearer {provider.api_key}"}
    return {}


def _build_base_url(provider: ProviderConfig, model: str) -> str:
    """Get the base URL for a request."""
    if provider.base_url:
        return provider.base_url.rstrip("/")
    # Default OpenAI-compatible
    prefix = model.split("/")[0] if "/" in model else model
    bases = {
        "openai": "https://api.openai.com",
        "ollama": "http://localhost:11434",
        "deepseek": "https://api.deepseek.com",
        "groq": "https://api.groq.com/openai/v1",
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "siliconflow": "https://api.siliconflow.cn/v1",
    }
    return bases.get(prefix, "https://api.openai.com")


async def stream_chat(
    config: NexusClawConfig,
    model: str,
    messages: list[dict],
) -> AsyncIterator[dict]:
    """
    Stream chat completion from the appropriate provider.
    Yields dicts: {"type": "token", "content": "..."} or {"type": "error", "error": "..."}
    """
    provider_name = model.split("/")[0] if "/" in model else config.default_provider
    provider = config.providers.get(provider_name)

    if not provider:
        # Fall back to default
        provider = config.providers.get(config.default_provider)
        if not provider:
            yield {"type": "error", "error": f"No provider configured for model '{model}'"}
            return

    base_url = _build_base_url(provider, model)
    auth = _get_auth_header(provider, model)

    # Determine actual model ID (strip provider prefix for provider-specific endpoints)
    actual_model = model
    # For OpenAI-compatible APIs, use the full model string as-is

    url = f"{base_url}/chat/completions"
    headers = {**auth, "Content-Type": "application/json"}
    if provider.api_key and "Authorization" not in auth:
        headers["Authorization"] = f"Bearer {provider.api_key}"

    payload = {
        "model": actual_model,
        "messages": messages,
        "stream": True,
    }

    try:
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
    except httpx.ConnectError:
        yield {"type": "error", "error": f"Cannot connect to {base_url}. Is the server running?"}
    except Exception as e:
        log.exception("chat.error")
        yield {"type": "error", "error": str(e)}


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
