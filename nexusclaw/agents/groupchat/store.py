"""
Group chat session store — in-memory.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GroupStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class GroupMessage:
    agent: str
    content: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {"agent": self.agent, "content": self.content, "timestamp": self.timestamp}


@dataclass
class GroupSession:
    id: str
    agent_ids: list[str]
    team_type: str  # "round_robin" | "selector"
    task: str
    status: GroupStatus = GroupStatus.PENDING
    messages: list[GroupMessage] = field(default_factory=list)
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_ids": self.agent_ids,
            "team_type": self.team_type,
            "task": self.task,
            "status": self.status.value if isinstance(self.status, GroupStatus) else str(self.status),
            "messages": [m.to_dict() for m in self.messages],
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class GroupStore:
    def __init__(self):
        self._sessions: dict[str, GroupSession] = {}

    def create(self, agent_ids: list[str], team_type: str, task: str) -> GroupSession:
        sid = str(uuid.uuid4())[:8]
        session = GroupSession(id=sid, agent_ids=agent_ids, team_type=team_type, task=task)
        self._sessions[sid] = session
        return session

    def get(self, sid: str) -> GroupSession | None:
        return self._sessions.get(sid)

    def list(self) -> list[GroupSession]:
        return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    def update_status(self, sid: str, status: GroupStatus, error: str | None = None):
        if sid in self._sessions:
            self._sessions[sid].status = status
            if error is not None:
                self._sessions[sid].error = error
            self._sessions[sid].updated_at = datetime.utcnow().isoformat()

    def add_message(self, sid: str, agent: str, content: str):
        if sid in self._sessions:
            self._sessions[sid].messages.append(GroupMessage(agent=agent, content=content))
            self._sessions[sid].updated_at = datetime.utcnow().isoformat()

    def delete(self, sid: str) -> bool:
        return bool(self._sessions.pop(sid, None))


GLOBAL_GROUP_STORE = GroupStore()
