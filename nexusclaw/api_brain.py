"""
Brain API — proxy to Mem0 Digital Brain at localhost:8765.
Proxifies Mem0 API so the web UI can talk to the brain without CORS issues.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/brain")

BRAIN_BASE = "http://host.docker.internal:8765"


class AddMemoryRequest(BaseModel):
    text: str
    user_id: str = "default"
    metadata: dict | None = None


class SearchRequest(BaseModel):
    query: str
    user_id: str = "default"
    limit: int = 10


class GetMemoryRequest(BaseModel):
    memory_id: str | None = None
    user_id: str = "default"


@router.get("/stats")
async def brain_stats():
    """Health check + memory count."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BRAIN_BASE}/health")
            resp.raise_for_status()
            data = resp.json()
            # Get memory count
            try:
                count_resp = await client.get(
                    f"{BRAIN_BASE}/v1/mem0/get",
                    params={"user_id": "default"},
                    json={},
                )
                count = 0
                if count_resp.status_code == 200:
                    results = count_resp.json().get("results", [])
                    count = len(results)
            except Exception:
                count = 0
            return {
                "status": "connected",
                "memory_count": count,
                "llm": data.get("llm"),
                "embedder": data.get("embedder"),
            }
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Digital Brain not running at localhost:8765")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def brain_search(body: SearchRequest):
    """Semantic search across memories."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{BRAIN_BASE}/v1/mem0/search",
                json={
                    "query": body.query,
                    "user_id": body.user_id,
                    "limit": body.limit,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Digital Brain not running at localhost:8765")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories")
async def brain_memories(user_id: str = "default"):
    """Get all memories for a user."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{BRAIN_BASE}/v1/mem0/get",
                json={"user_id": user_id},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Digital Brain not running at localhost:8765")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memories")
async def brain_add_memory(body: AddMemoryRequest):
    """Add a new memory."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {"text": body.text, "user_id": body.user_id}
            if body.metadata:
                payload["metadata"] = body.metadata
            resp = await client.post(f"{BRAIN_BASE}/v1/mem0/add", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Digital Brain not running at localhost:8765")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
async def brain_delete_memory(memory_id: str, user_id: str = "default"):
    """Delete a memory."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                f"{BRAIN_BASE}/v1/mem0/delete/{memory_id}",
                params={"user_id": user_id},
            )
            resp.raise_for_status()
            return {"ok": True}
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Digital Brain not running at localhost:8765")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
