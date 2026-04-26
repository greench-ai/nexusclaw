"""
NexusClaw Provider Engine
Supports: Ollama, OpenAI, Anthropic, Minimaxi, OpenRouter, Custom
"""
import os
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator

class BaseProvider(ABC):
    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        pass
    
    @abstractmethod
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        pass

class OllamaProvider(BaseProvider):
    """Local Ollama — free, private, no API key needed."""
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        super().__init__(base_url=base_url, model=model)
    
    async def chat(self, messages: list[dict], **kwargs) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {"model": self.model, "messages": messages, "stream": False}
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                data = await resp.json()
                return data["message"]["content"]
    
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {"model": self.model, "messages": messages, "stream": True}
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                async for line in resp.content:
                    if line:
                        import json
                        chunk = json.loads(line)
                        if "content" in chunk.get("message", {}):
                            yield chunk["message"]["content"]

class OpenAIProvider(BaseProvider):
    """OpenAI GPT models."""
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key=api_key, model=model, base_url="https://api.openai.com/v1")
    
    async def chat(self, messages: list[dict], **kwargs) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self.model, "messages": messages, **kwargs}
            async with session.post(f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self.model, "messages": messages, "stream": True, **kwargs}
            async with session.post(f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: "):
                            if text == "data: [DONE]":
                                break
                            import json
                            chunk = json.loads(text[6:])
                            if delta := chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                                yield delta

class MinimaxiProvider(BaseProvider):
    """Minimaxi M2.7-highspeed — fast and cheap."""
    def __init__(self, api_key: str, model: str = "MiniMax-M2.7-highspeed"):
        super().__init__(api_key=api_key, model=model, base_url="https://api.minimax.io/v1")
    
    async def chat(self, messages: list[dict], **kwargs) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self.model, "messages": messages, **kwargs}
            async with session.post(f"{self.base_url}/text/chatcompletion_v2", json=payload, headers=headers) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self.model, "messages": messages, "stream": True, **kwargs}
            async with session.post(f"{self.base_url}/text/chatcompletion_v2", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: "):
                            if text == "data: [DONE]":
                                break
                            import json
                            chunk = json.loads(text[6:])
                            if delta := chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                                yield delta

class AnthropicProvider(BaseProvider):
    """Anthropic Claude models."""
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key=api_key, model=model, base_url="https://api.anthropic.com/v1")
    
    async def chat(self, messages: list[dict], **kwargs) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            # Convert messages format
            system = next((m["content"] for m in messages if m.get("role") == "system"), "")
            msgs = [m for m in messages if m.get("role") != "system"]
            payload = {"model": self.model, "messages": msgs, "system": system, **kwargs}
            async with session.post(f"{self.base_url}/messages", json=payload, headers=headers) as resp:
                data = await resp.json()
                return data["content"][0]["text"]
    
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            system = next((m["content"] for m in messages if m.get("role") == "system"), "")
            msgs = [m for m in messages if m.get("role") != "system"]
            payload = {"model": self.model, "messages": msgs, "system": system, "stream": True, **kwargs}
            async with session.post(f"{self.base_url}/messages", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: "):
                            if text == "data: [DONE]":
                                break
                            import json
                            chunk = json.loads(text[6:])
                            if chunk.get("type") == "content_block_delta":
                                yield chunk.get("delta", {}).get("text", "")

def create_provider(provider: str, api_key: str = "", base_url: str = "", model: str = "") -> BaseProvider:
    """Factory: create any provider by name."""
    providers = {
        "ollama": OllamaProvider,
        "local": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "minimaxi": MinimaxiProvider,
    }
    cls = providers.get(provider.lower(), OllamaProvider)
    return cls(api_key=api_key, base_url=base_url, model=model)
