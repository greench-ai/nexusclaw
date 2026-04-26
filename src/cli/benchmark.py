#!/usr/bin/env python3
"""
NexusClaw Benchmark Tool
Measure latency, throughput, and quality across providers.
"""
import asyncio, time, json, statistics, sys
from typing import Callable

async def measure_latency(provider_fn: Callable, runs: int = 5) -> dict:
    """Measure average latency over N runs."""
    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        await provider_fn()
        latencies.append((time.perf_counter() - start) * 1000)  # ms
    
    return {
        "avg_ms": round(statistics.mean(latencies), 1),
        "min_ms": round(min(latencies), 1),
        "max_ms": round(max(latencies), 1),
        "median_ms": round(statistics.median(latencies), 1),
        "stddev": round(statistics.stdev(latencies), 1) if len(latencies) > 1 else 0,
        "runs": runs
    }

async def benchmark_ollama(model: str = "llama3.2", prompt: str = "Say 'hello' in one sentence.") -> dict:
    """Benchmark Ollama."""
    import aiohttp
    
    async def call():
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                await resp.json()
    
    result = await measure_latency(call)
    result["provider"] = "ollama"
    result["model"] = model
    result["prompt_chars"] = len(prompt)
    return result

async def benchmark_openai(model: str = "gpt-4o-mini", prompt: str = "Say 'hello' in one sentence.") -> dict:
    """Benchmark OpenAI."""
    import os, aiohttp
    
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set", "provider": "openai", "model": model}
    
    async def call():
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                await resp.json()
    
    result = await measure_latency(call)
    result["provider"] = "openai"
    result["model"] = model
    result["prompt_chars"] = len(prompt)
    return result

async def benchmark_all():
    """Run all benchmarks."""
    print("\n⚡ NexusClaw Benchmark\n" + "="*50)
    
    tests = [
        ("Ollama (llama3.2)", benchmark_ollama("llama3.2")),
        ("Ollama (qwen2.5)", benchmark_ollama("qwen2.5-coder:7b")),
        ("OpenAI (gpt-4o-mini)", benchmark_openai("gpt-4o-mini")),
    ]
    
    results = []
    for name, task in tests:
        print(f"\n🔄 {name}...")
        try:
            result = await asyncio.wait_for(task, timeout=120)
            if "error" in result:
                print(f"  ⚠️  Skipped: {result['error']}")
            else:
                print(f"  ✅ Avg: {result['avg_ms']}ms | Min: {result['min_ms']}ms | Max: {result['max_ms']}ms | StdDev: {result['stddev']}ms")
                results.append(result)
        except asyncio.TimeoutError:
            print(f"  ❌ Timeout")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    if results:
        fastest = min(results, key=lambda x: x["avg_ms"])
        print(f"\n🏆 Fastest: {fastest['provider']}/{fastest['model']} ({fastest['avg_ms']}ms avg)")
        
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved to benchmark_results.json")
    
    print()
    return results

if __name__ == "__main__":
    asyncio.run(benchmark_all())
