"""
NexusClaw Webhook Engine
Trigger external services on events.
"""
import os, json, asyncio, hashlib, hmac
from datetime import datetime
import aiohttp

@dataclass
class Webhook:
    id: str
    url: str
    events: list
    secret: str
    enabled: bool = True
    retry_count: int = 3
    retry_delay: float = 5.0

from dataclasses import dataclass

class WebhookEngine:
    def __init__(self, storage_path: str = "~/.nexusclaw/webhooks.json"):
        self.storage_path = os.path.expanduser(storage_path)
        self.webhooks: list[Webhook] = []
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                data = json.load(f)
                for w in data.get("webhooks", []):
                    self.webhooks.append(Webhook(**w))
    
    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump({"webhooks": [w.__dict__ for w in self.webhooks]}, f, indent=2, default=str)
    
    def register(self, url: str, events: list, secret: str = "") -> str:
        webhook_id = hashlib.sha256(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        secret = secret or hashlib.sha256(webhook_id.encode()).hexdigest()[:32]
        webhook = Webhook(id=webhook_id, url=url, events=events, secret=secret)
        self.webhooks.append(webhook)
        self._save()
        return webhook_id
    
    def unregister(self, webhook_id: str) -> bool:
        self.webhooks = [w for w in self.webhooks if w.id != webhook_id]
        self._save()
        return True
    
    async def dispatch(self, event: str, payload: dict) -> list[dict]:
        results = []
        for webhook in self.webhooks:
            if not webhook.enabled or event not in webhook.events:
                continue
            result = await self._send(webhook, event, payload)
            results.append({"webhook_id": webhook.id, "result": result})
        return results
    
    async def _send(self, webhook: Webhook, event: str, payload: dict) -> dict:
        headers = {"Content-Type": "application/json", "X-NexusClaw-Event": event}
        if webhook.secret:
            headers["X-NexusClaw-Signature"] = hmac.new(
                webhook.secret.encode(), json.dumps(payload).encode(), hashlib.sha256).hexdigest()
        
        body = {"event": event, "timestamp": datetime.utcnow().isoformat(), "data": payload}
        
        for attempt in range(webhook.retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook.url, json=body, headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.ok:
                            return {"ok": True, "status": resp.status}
                        elif resp.status >= 500:
                            await asyncio.sleep(webhook.retry_delay * (attempt + 1))
                            continue
                        return {"ok": False, "status": resp.status}
            except Exception as e:
                if attempt == webhook.retry_count - 1:
                    return {"ok": False, "error": str(e)}
                await asyncio.sleep(webhook.retry_delay * (attempt + 1))
        return {"ok": False, "error": "max retries"}
    
    async def on_attack_found(self, container: str, wallet: str):
        return await self.dispatch("attack_found", {"container": container, "wallet": wallet, "found": True})
    
    async def on_goal_completed(self, goal_id: str, title: str, result: str):
        return await self.dispatch("goal_completed", {"goal_id": goal_id, "title": title, "result": result[:500]})
    
    async def on_heartbeat(self, count: int):
        return await self.dispatch("heartbeat", {"heartbeat": count})
