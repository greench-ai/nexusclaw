"""
NexusClaw Model Gateway
Unified gateway for all AI providers — Ollama, OpenAI, Anthropic, Minimaxi.
"""
import os, json, asyncio
from typing import AsyncIterator

class ModelGateway:
    """Single gateway for all model providers."""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = os.environ.get("NEXUS_PROVIDER", "ollama")
        self.default_model = os.environ.get("NEXUS_MODEL", "llama3.2")
    
    async def chat(self, messages: list, provider: str = None, model: str = None, stream: bool = True) -> AsyncIterator[str]:
        provider = provider or self.default_provider
        model = model or self.default_model
        
        if provider in ("ollama", "local"):
            async for chunk in self.ollama_chat(model, messages):
                yield chunk
        elif provider == "openai":
            async for chunk in self.openai_chat(model, messages):
                yield chunk
        elif provider == "anthropic":
            async for chunk in self.anthropic_chat(model, messages):
                yield chunk
        elif provider == "minimaxi":
            async for chunk in self.minimaxi_chat(model, messages):
                yield chunk
    
    async def ollama_chat(self, model: str, messages: list) -> AsyncIterator[str]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {"model": model, "messages": messages, "stream": True}
            async with session.post("http://localhost:11434/api/chat", json=payload) as resp:
                async for line in resp.content:
                    if line:
                        chunk = json.loads(line)
                        if "content" in chunk.get("message", {}):
                            yield chunk["message"]["content"]
    
    async def openai_chat(self, model: str, messages: list) -> AsyncIterator[str]:
        import aiohttp
        api_key = os.environ.get("OPENAI_API_KEY", "")
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {"model": model, "messages": messages, "stream": True}
            async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: ") and text != "data: [DONE]":
                            chunk = json.loads(text[6:])
                            if delta := chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                                yield delta
    
    async def anthropic_chat(self, model: str, messages: list) -> AsyncIterator[str]:
        # Similar to openai but with Anthropic API format
        yield "[Anthropic streaming not implemented]"
    
    async def minimaxi_chat(self, model: str, messages: list) -> AsyncIterator[str]:
        import aiohttp
        api_key = os.environ.get("MINIMAXI_API_KEY", "")
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {"model": model, "messages": messages, "stream": True}
            async with session.post("https://api.minimax.io/v1/text/chatcompletion_v2", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: ") and text != "data: [DONE]":
                            chunk = json.loads(text[6:])
                            if delta := chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                                yield delta
