"""
Agent API — session management and agent execution.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from nexusclaw.agents.session import GLOBAL_STORE, AgentStatus
from nexusclaw.agents.runtime import run_agent
from nexusclaw.agents.tools import GLOBAL_REGISTRY

router = APIRouter(prefix="/api/v1/agents")


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateSessionBody(BaseModel):
    task: str


class ToolCallInput(BaseModel):
    tool: str
    input: dict = {}


# ── Session CRUD ──────────────────────────────────────────────────────────────

@router.get("")
async def list_sessions():
    """List all agent sessions."""
    sessions = GLOBAL_STORE.list()
    return {"sessions": [s.to_dict() for s in sessions]}


@router.post("/sessions")
async def create_session(body: CreateSessionBody):
    """Create a new agent session and start running it."""
    session = GLOBAL_STORE.create(body.task)
    return session.to_dict()


@router.get("/sessions/{sid}")
async def get_session(sid: str):
    """Get a specific session."""
    session = GLOBAL_STORE.get(sid)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    return session.to_dict()


@router.delete("/sessions/{sid}")
async def delete_session(sid: str):
    """Delete a session."""
    deleted = GLOBAL_STORE.delete(sid)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    return {"ok": True}


# ── Tools ─────────────────────────────────────────────────────────────────────

@router.get("/tools")
async def list_tools():
    """List all available tools."""
    return {"tools": GLOBAL_REGISTRY.list_tools()}


@router.post("/tools/call")
async def call_tool(body: ToolCallInput):
    """Call a specific tool directly."""
    tool = GLOBAL_REGISTRY.get(body.tool)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{body.tool}' not found")
    result = await tool.run(**body.input)
    return result


# ── WebSocket streaming ───────────────────────────────────────────────────────

@router.websocket("/stream/{session_id}")
async def agent_stream(ws: WebSocket, session_id: str):
    """
    Stream agent execution for a session.
    Send: {{"type": "start"}} or just connect after creating session.
    Receives: token, tool_call, tool_result, done, error events.
    """
    await ws.accept()

    session = GLOBAL_STORE.get(session_id)
    if not session:
        await ws.send_json({"type": "error", "error": f"Session {session_id} not found"})
        await ws.close()
        return

    try:
        await ws.send_json({"type": "start", "session_id": session_id})

        async for event in run_agent(session_id, session.task):
            await ws.send_json(event)
            if event["type"] == "done":
                break
            if event["type"] == "error":
                break

    except WebSocketDisconnect:
        pass
