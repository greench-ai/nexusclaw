"""
NexusClaw Vector Memory — Qdrant-backed persistent memory
Stores experiences, reflections, and conversation history as embeddings.
"""
import os, json, uuid, time
from typing import Optional, list
from dataclasses import dataclass, field
from datetime import datetime

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = "nexusclaw_memory"

@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

class VectorMemory:
    """Qdrant-backed vector memory store."""
    
    def __init__(self, url: str = QDRANT_URL, collection: str = COLLECTION):
        self.url = url
        self.collection = collection
        self._client = None
        self._ready = False
    
    def _get_client(self):
        """Lazy init Qdrant client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(base_url=self.url, timeout=5.0)
                self._ensure_collection()
                self._ready = True
            except Exception as e:
                print(f"Qdrant not available: {e}")
                self._ready = False
        return self._client
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        import httpx
        client = self._client
        try:
            resp = client.get(f"/collections/{self.collection}")
            if resp.status_code == 404:
                # Create collection
                client.put(f"/collections/{self.collection}", json={
                    "vectors": {"size": 384, "distance": "Cosine"}
                })
                print(f"Created Qdrant collection: {self.collection}")
        except Exception as e:
            print(f"Collection check failed: {e}")
    
    def add(self, content: str, metadata: dict = {}) -> str:
        """Add a memory entry. Returns entry ID."""
        if not self._ready:
            self._get_client()
        
        entry_id = str(uuid.uuid4())
        
        if self._ready:
            try:
                import httpx
                embedding = self._embed(content)
                payload = {
                    "id": entry_id,
                    "vector": embedding,
                    "payload": {"content": content, "metadata": metadata, "created_at": datetime.utcnow().isoformat() + "Z"}
                }
                self._client.put(f"/collections/{self.collection}/points", json={"points": [payload]})
            except Exception as e:
                print(f"Qdrant add failed: {e}")
        
        return entry_id
    
    def search(self, query: str, limit: int = 5, filter_metadata: dict = None) -> list[dict]:
        """Search memories by semantic similarity."""
        if not self._ready:
            return []
        
        try:
            import httpx
            embedding = self._embed(query)
            search_payload = {
                "vector": embedding,
                "limit": limit,
                "with_payload": True
            }
            if filter_metadata:
                search_payload["filter"] = filter_metadata
            
            resp = self._client.post(f"/collections/{self.collection}/points/search", json=search_payload)
            if resp.status_code == 200:
                results = resp.json().get("result", [])
                return [
                    {"id": r["id"], "score": r["score"], "content": r["payload"]["content"],
                     "metadata": r["payload"].get("metadata", {}), "created_at": r["payload"].get("created_at")}
                    for r in results
                ]
        except Exception as e:
            print(f"Search failed: {e}")
        
        return []
    
    def get(self, entry_id: str) -> Optional[dict]:
        """Get a specific memory by ID."""
        if not self._ready:
            return None
        
        try:
            resp = self._client.get(f"/collections/{self.collection}/points/{entry_id}")
            if resp.status_code == 200:
                r = resp.json().get("result", {})
                return {"id": r["id"], "content": r["payload"]["content"],
                        "metadata": r["payload"].get("metadata", {}),
                        "created_at": r["payload"].get("created_at")}
        except: pass
        return None
    
    def delete(self, entry_id: str) -> bool:
        """Delete a memory by ID."""
        if not self._ready:
            return False
        
        try:
            resp = self._client.delete(f"/collections/{self.collection}/points/{entry_id}")
            return resp.status_code in (200, 404)
        except:
            return False
    
    def count(self) -> int:
        """Count total memories."""
        if not self._ready:
            return 0
        try:
            resp = self._client.get(f"/collections/{self.collection}")
            if resp.status_code == 200:
                return resp.json().get("result", {}).get("points_count", 0)
        except: pass
        return 0
    
    def _embed(self, text: str) -> list[float]:
        """Generate embedding for text using local model or API."""
        # Try Ollama first
        try:
            import httpx
            resp = httpx.post(f"{os.environ.get('OLLAMA_URL','http://localhost:11434')}/api/embed", 
                            json={"model": "nomic-embed-text", "input": text}, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embeddings", [[]])[0]
        except: pass
        
        # Fallback: random embedding
        import random
        return [random.uniform(-1, 1) for _ in range(384)]

# Convenience functions
_store = None

def get_store() -> VectorMemory:
    global _store
    if _store is None:
        _store = VectorMemory()
    return _store

def remember(content: str, metadata: dict = {}) -> str:
    """Store a memory."""
    return get_store().add(content, metadata)

def recall(query: str, limit: int = 5) -> list[dict]:
    """Search memories."""
    return get_store().search(query, limit=limit)

def forget(entry_id: str) -> bool:
    """Delete a memory."""
    return get_store().delete(entry_id)

if __name__ == "__main__":
    vm = VectorMemory()
    print(f"VectorMemory ready. Collection: {COLLECTION}")
    print(f"Total memories: {vm.count()}")
