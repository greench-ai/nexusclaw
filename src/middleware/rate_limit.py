"""
NexusClaw Rate Limiter + Cost Tracker
Track usage, limit requests, estimate costs.
"""
import os, json, time, asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class CostEntry:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: str

# Token costs per 1M tokens (approximate)
TOKEN_COSTS = {
    "openai": {
        "gpt-4o": (2.5, 10.0),
        "gpt-4o-mini": (0.15, 0.6),
        "o1": (15.0, 60.0),
        "o1-mini": (1.1, 4.4),
        "gpt-4-turbo": (10.0, 30.0),
    },
    "anthropic": {
        "claude-3-5-sonnet": (3.0, 15.0),
        "claude-3-5-haiku": (0.25, 1.25),
        "claude-3-opus": (15.0, 75.0),
    },
    "ollama": {"default": (0, 0)},  # Free
    "minimaxi": {"default": (0.1, 0.1)},  # Approximate
    "openrouter": {"default": (0.5, 0.5)},  # Varies
}

class RateLimiter:
    """
    Token bucket rate limiter per user/provider.
    """
    def __init__(self, storage_path: str = "~/.nexusclaw/rate_limits.json"):
        self.storage_path = os.path.expanduser(storage_path)
        self.buckets: dict[str, dict] = {}
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                self.buckets = json.load(f)
    
    def _save(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.buckets, f, indent=2)
    
    def _key(self, user_id: str, provider: str) -> str:
        return f"{user_id}:{provider}"
    
    def check(self, user_id: str, provider: str, cost: int = 1) -> tuple[bool, dict]:
        """
        Check if request is allowed. Returns (allowed, info).
        """
        bucket = self.buckets.get(self._key(user_id, provider), {
            "tokens": 100, "rate": 20, "interval": 60, "last_refill": time.time()
        })
        
        now = time.time()
        elapsed = now - bucket["last_refill"]
        
        # Refill tokens
        refill = elapsed * (bucket["rate"] / bucket["interval"])
        bucket["tokens"] = min(bucket["tokens"] + refill, bucket["rate"])
        bucket["last_refill"] = now
        
        allowed = bucket["tokens"] >= cost
        if allowed:
            bucket["tokens"] -= cost
        
        self.buckets[self._key(user_id, provider)] = bucket
        self._save()
        
        return allowed, {
            "tokens_remaining": int(bucket["tokens"]),
            "rate": bucket["rate"],
            "reset_in": int(bucket["interval"] - elapsed) if elapsed < bucket["interval"] else 0
        }
    
    def set_limit(self, user_id: str, provider: str, rate: int, interval: int = 60):
        """Set rate limit for user/provider."""
        key = self._key(user_id, provider)
        if key in self.buckets:
            self.buckets[key]["rate"] = rate
            self.buckets[key]["interval"] = interval
        else:
            self.buckets[key] = {"tokens": rate, "rate": rate, "interval": interval, "last_refill": time.time()}
        self._save()

class CostTracker:
    """
    Track API usage and estimate costs.
    """
    def __init__(self, storage_path: str = "~/.nexusclaw/costs.json"):
        self.storage_path = os.path.expanduser(storage_path)
        self.entries: list[CostEntry] = []
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                data = json.load(f)
                self.entries = [CostEntry(**e) for e in data.get("entries", [])]
    
    def _save(self):
        with open(self.storage_path, "w") as f:
            json.dump({"entries": [
                {**e.__dict__, "timestamp": e.timestamp} for e in self.entries
            ]}, f, indent=2, default=str)
    
    def log(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        """Log a cost entry."""
        costs = TOKEN_COSTS.get(provider, {}).get(model, TOKEN_COSTS.get(provider, {}).get("default", (0, 0)))
        cost_usd = (input_tokens / 1_000_000 * costs[0] + output_tokens / 1_000_000 * costs[1])
        
        self.entries.append(CostEntry(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 6),
            timestamp=datetime.utcnow().isoformat()
        ))
        self._save()
    
    def total_cost(self, days: int = 30) -> dict:
        """Get total cost over N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [e for e in self.entries if datetime.fromisoformat(e.timestamp) > cutoff]
        
        by_provider = defaultdict(lambda: {"cost": 0, "requests": 0, "input_tokens": 0, "output_tokens": 0})
        for e in recent:
            by_provider[e.provider]["cost"] += e.cost_usd
            by_provider[e.provider]["requests"] += 1
            by_provider[e.provider]["input_tokens"] += e.input_tokens
            by_provider[e.provider]["output_tokens"] += e.output_tokens
        
        return {
            "total_usd": round(sum(v["cost"] for v in by_provider.values()), 4),
            "total_requests": len(recent),
            "days": days,
            "by_provider": dict(by_provider)
        }
    
    def budget_check(self, monthly_budget_usd: float) -> dict:
        """Check if within monthly budget."""
        total = self.total_cost(days=30)["total_usd"]
        remaining = monthly_budget_usd - total
        return {
            "budget": monthly_budget_usd,
            "spent": round(total, 4),
            "remaining": round(remaining, 4),
            "percent_used": round(total / monthly_budget_usd * 100, 1) if monthly_budget_usd > 0 else 0,
            "over_budget": total > monthly_budget_usd
        }

# Global instances
_limiter = None
_tracker = None

def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter

def get_cost_tracker() -> CostTracker:
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
