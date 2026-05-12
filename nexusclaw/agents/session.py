"""
Agent session store — in-memory store for running agent sessions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class ToolCall:
    def __init__(self, tool: str, input: dict):
        self.id = str(uuid.uuid4())[:8]
        self.tool = tool
        self.input = input
        self.output: str | None = None
        self.error: str | None = None
        self.started_at: str | None = None
        self.completed_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tool": self.tool,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class AgentSession:
    id: str
    task: str
    status: AgentStatus = AgentStatus.IDLE
    messages: list[dict] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        status_val = self.status.value if isinstance(self.status, AgentStatus) else str(self.status)
        return {
            "id": self.id,
            "task": self.task,
            "status": status_val,
            "messages": self.messages,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "artifacts": self.artifacts,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}

    def create(self, task: str) -> AgentSession:
        sid = str(uuid.uuid4())[:8]
        session = AgentSession(id=sid, task=task)
        self._sessions[sid] = session
        return session

    def get(self, sid: str) -> AgentSession | None:
        return self._sessions.get(sid)

    def list(self) -> list[AgentSession]:
        return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    def update(self, sid: str, **kwargs):
        if sid in self._sessions:
            session = self._sessions[sid]
            for k, v in kwargs.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            session.updated_at = datetime.utcnow().isoformat()

    def delete(self, sid: str) -> bool:
        return bool(self._sessions.pop(sid, None))

    def add_message(self, sid: str, role: str, content: str):
        if sid in self._sessions:
            self._sessions[sid].messages.append({"role": role, "content": content, "created_at": datetime.utcnow().isoformat()})
            self._sessions[sid].updated_at = datetime.utcnow().isoformat()

    def add_tool_call(self, sid: str, tool: str, tool_input: dict) -> ToolCall:
        tc = ToolCall(tool, tool_input)
        if sid in self._sessions:
            self._sessions[sid].tool_calls.append(tc)
        return tc

    def complete_tool_call(self, sid: str, tc_id: str, output: str, error: str | None = None):
        if sid in self._sessions:
            for tc in self._sessions[sid].tool_calls:
                if tc.id == tc_id:
                    tc.output = output
                    tc.error = error
                    tc.completed_at = datetime.utcnow().isoformat()
                    break

    def add_artifact(self, sid: str, artifact: dict):
        if sid in self._sessions:
            self._sessions[sid].artifacts.append(artifact)


# Global store
GLOBAL_STORE = SessionStore()
