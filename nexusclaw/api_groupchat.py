"""
Group Chat API — REST endpoints for AutoGen multi-agent group chat.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from nexusclaw.agents.groupchat.store import GLOBAL_GROUP_STORE
from nexusclaw.agents.groupchat.runner import run_group_chat

router = APIRouter(prefix="/api/v1/group-chat")


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateSessionBody(BaseModel):
    agent_ids: list[str]
    team_type: str = "round_robin"  # "round_robin" | "selector"
    message: str


# ── REST ──────────────────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions():
    """List all group chat sessions."""
    sessions = GLOBAL_GROUP_STORE.list()
    return [s.to_dict() for s in sessions]


@router.post("/sessions")
async def create_session(body: CreateSessionBody):
    """Create and start a group chat session."""
    if not body.agent_ids:
        raise HTTPException(status_code=400, detail="No agents selected")
    if not body.message:
        raise HTTPException(status_code=400, detail="Task/message is required")

    session = GLOBAL_GROUP_STORE.create(
        agent_ids=body.agent_ids,
        team_type=body.team_type,
        task=body.message,
    )
    # Start the group chat in background
    import asyncio
    asyncio.create_task(_run_and_forget(session.id, body.agent_ids, body.team_type, body.message))
    return session.to_dict()


async def _run_and_forget(sid: str, agent_ids: list[str], team_type: str, message: str):
    """Run group chat and discard events (store is updated by runner)."""
    try:
        async for _ in run_group_chat(sid, agent_ids, team_type, message):
            pass
    except Exception as e:
        from nexusclaw.agents.groupchat.store import GroupStatus
        GLOBAL_GROUP_STORE.update_status(sid, GroupStatus.ERROR, error=str(e))


@router.get("/sessions/{sid}")
async def get_session(sid: str):
    """Get a session with its messages."""
    session = GLOBAL_GROUP_STORE.get(sid)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    return session.to_dict()


@router.delete("/sessions/{sid}")
async def delete_session(sid: str):
    """Delete a session."""
    deleted = GLOBAL_GROUP_STORE.delete(sid)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    return {"ok": True}


# ── WebSocket — streaming ──────────────────────────────────────────────────────

@router.websocket("/sessions/{sid}/stream")
async def groupchat_stream(ws: WebSocket, sid: str):
    """WebSocket stream of group chat events."""
    await ws.accept()

    session = GLOBAL_GROUP_STORE.get(sid)
    if not session:
        await ws.send_json({"type": "error", "error": f"Session {sid} not found"})
        await ws.close()
        return

    try:
        async for event in run_group_chat(
            sid,
            session.agent_ids,
            session.team_type,
            session.task,
        ):
            await ws.send_json(event)
            if event.get("type") in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
