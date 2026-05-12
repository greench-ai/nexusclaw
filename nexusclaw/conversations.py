"""
Conversation storage — SQLite.
Stores conversations + messages for chat history persistence.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

DB_PATH = Path.home() / ".nexusclaw" / "conversations.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT 'New conversation',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conv
            ON messages(conversation_id, created_at);
    """)
    conn.commit()


def _now() -> str:
    return datetime.utcnow().isoformat()


def create_conversation(title: str = "New conversation") -> dict[str, Any]:
    """Create a new conversation. Returns the conversation dict."""
    import uuid
    cid = str(uuid.uuid4())[:8]
    now = _now()
    conn = _get_db()
    conn.execute(
        "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (cid, title, now, now),
    )
    conn.commit()
    conn.close()
    return {"id": cid, "title": title, "created_at": now, "updated_at": now}


def list_conversations() -> list[dict[str, Any]]:
    """List all conversations, newest first."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conv_id: str) -> dict[str, Any] | None:
    conn = _get_db()
    row = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
        (conv_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_messages(conv_id: str) -> list[dict[str, Any]]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, conversation_id, role, content, model, created_at "
        "FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_message(
    conv_id: str,
    role: str,
    content: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Add a message to a conversation. Also updates conversation.updated_at."""
    now = _now()
    conn = _get_db()
    cur = conn.execute(
        "INSERT INTO messages (conversation_id, role, content, model, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (conv_id, role, content, model, now),
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conv_id),
    )
    conn.commit()
    msg_id = cur.lastrowid
    conn.close()
    return {
        "id": msg_id,
        "conversation_id": conv_id,
        "role": role,
        "content": content,
        "model": model,
        "created_at": now,
    }


def update_conversation_title(conv_id: str, title: str) -> dict[str, Any] | None:
    now = _now()
    conn = _get_db()
    conn.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (title, now, conv_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
        (conv_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_conversation(conv_id: str) -> bool:
    conn = _get_db()
    cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted
