"""
NexusClaw Model Gateway — Unified streaming for all AI providers.
Handles: Ollama, OpenAI, Anthropic, Minimaxi, OpenRouter, Custom.
"""
import os, json, asyncio
from typing import AsyncIterator, Optional
from dataclasses import dataclass
import aiohttp

PROVIDERS = {
    "ollama": {"base": "http://localhost:11434/v1", "stream": True},
    "openai": {"base": "https://api.openai.com/v1", "stream": True},
    "anthropic": {"base": "https://api.anthropic.com/v1", "stream": True},
    "minimaxi": {"base": "https://api.minimaxi.chat/v1", "stream": True},
    "openrouter": {"base": "https://openrouter.ai/api/v1", "stream": True},
    "custom": {"base": os.environ.get("CUSTOM_API_URL", "http://localhost:8080/v1"), "stream": True}
}

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class ChatResponse:
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None

class ModelGateway:
    """
    Unified gateway for all AI providers.
    Send the same format to any provider.
    """
    
    def __init__(self, api_keys: dict = None):
        self.api_keys = api_keys or {}
    
    async def chat(
        self,
        provider: str,
        model: str,
        messages: list[dict],
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[str] | ChatResponse:
        """
        Send chat request to any provider.
        Yields text chunks if stream=True, returns full response if stream=False.
        """
        config = PROVIDERS.get(provider, PROVIDERS["ollama"])
        base_url = config["base"]
        
        headers = {"Content-Type": "application/json"}
        
        if provider == "openai":
            headers["Authorization"] = f"Bearer {self.api_keys.get('openai', '')}"
        elif provider == "anthropic":
            headers["x-api-key"] = self.api_keys.get("anthropic", "")
            headers["anthropic-version"] = "2023-06-01"
            # Anthropic uses different message format
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "stream": stream
            }
        elif provider == "minimaxi":
            headers["Authorization"] = f"Bearer {self.api_keys.get('minimaxi', '')}"
        elif provider == "openrouter":
            headers["HTTP-Referer"] = "https://nexusclaw.ai"
            headers["X-Title"] = "NexusClaw"
            headers["Authorization"] = f"Bearer {self.api_keys.get('openrouter', '')}"
        else:
            # Ollama, custom
            headers["Authorization"] = f"Bearer {self.api_keys.get(provider, 'local')}"
        
        # Build payload
        if provider == "anthropic":
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "stream": stream,
                "temperature": temperature
            }
        else:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Provider error {resp.status}: {text}")
                
                if stream:
                    async for line in resp.content:
                        line = line.decode().strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            if provider == "anthropic":
                                if data.get("type") == "content_block_delta":
                                    yield data.get("delta", {}).get("text", "")
                            else:
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                else:
                    data = await resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return ChatResponse(
                        content=content,
                        model=model,
                        provider=provider,
                        usage=data.get("usage"),
                        finish_reason=data.get("choices", [{}])[0].get("finish_reason")
                    )

    async def list_models(self, provider: str) -> list[str]:
        """List available models for a provider."""
        if provider == "ollama":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:11434/api/tags") as resp:
                        if resp.ok:
                            data = await resp.json()
                            return [m["name"] for m in data.get("models", [])]
            except: pass
        return []

    async def health_check(self, provider: str) -> bool:
        """Check if a provider is reachable."""
        try:
            async with aiohttp.ClientSession() as session:
                if provider == "ollama":
                    async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                        return resp.ok
                elif provider == "openai":
                    async with session.get("https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {self.api_keys.get('openai', '')}"},
                        timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        return resp.ok
        except:
            return False
        return False

# CLI for testing
async def main():
    import sys
    gateway = ModelGateway()
    provider = sys.argv[1] if len(sys.argv) > 1 else "ollama"
    model = sys.argv[2] if len(sys.argv) > 2 else "llama3.2"
    message = sys.argv[3] if len(sys.argv) > 3 else "Say hello in one sentence."
    
    print(f"Provider: {provider}/{model}")
    print(f"Message: {message}")
    print("Response: ", end="", flush=True)
    
    chunks = []
    async for chunk in gateway.chat(provider, model, [{"role": "user", "content": message}]):
        print(chunk, end="", flush=True)
        chunks.append(chunk)
    
    print("\n\nDone. Total chunks:", len(chunks))

if __name__ == "__main__":
    asyncio.run(main())
