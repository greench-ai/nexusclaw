"""
Prompt template storage — SQLite.
Stores named prompt templates with variable interpolation.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path.home() / ".nexusclaw" / "prompt_templates.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL,
            user_prompt_template TEXT NOT NULL DEFAULT '',
            focus_mode TEXT NOT NULL DEFAULT 'copilot',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()


def _now() -> str:
    return datetime.utcnow().isoformat()


def _extract_vars(template: str) -> list[str]:
    """Extract {{variable}} placeholders from a template string."""
    return list(set(re.findall(r'\{\{(\w+)\}\}', template)))


class PromptTemplate:
    def __init__(self, row: dict):
        self.id = row["id"]
        self.name = row["name"]
        self.description = row["description"]
        self.system_prompt = row["system_prompt"]
        self.user_prompt_template = row["user_prompt_template"]
        self.focus_mode = row["focus_mode"]
        self.created_at = row["created_at"]
        self.updated_at = row["updated_at"]

    def interpolate(self, **kwargs) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) with vars substituted."""
        system = self.system_prompt
        for key, val in kwargs.items():
            system = system.replace(f"{{{{{key}}}}}", str(val))
        user = self.user_prompt_template
        for key, val in kwargs.items():
            user = user.replace(f"{{{{{key}}}}}", str(val))
        return system, user

    def to_dict(self) -> dict:
        vars_ = _extract_vars(self.system_prompt + self.user_prompt_template)
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "focus_mode": self.focus_mode,
            "variables": vars_,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def list_templates() -> list[dict]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM templates ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [PromptTemplate(dict(r)).to_dict() for r in rows]


def get_template(name: str) -> dict | None:
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM templates WHERE name = ?", (name,)
    ).fetchone()
    conn.close()
    return PromptTemplate(dict(row)).to_dict() if row else None


def create_template(
    name: str,
    system_prompt: str,
    user_prompt_template: str = "",
    description: str = "",
    focus_mode: str = "copilot",
) -> dict:
    import uuid
    tid = str(uuid.uuid4())[:8]
    now = _now()
    conn = _get_db()
    conn.execute(
        "INSERT INTO templates (id, name, description, system_prompt, user_prompt_template, focus_mode, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (tid, name, description, system_prompt, user_prompt_template, focus_mode, now, now),
    )
    conn.commit()
    conn.close()
    return PromptTemplate({
        "id": tid, "name": name, "description": description,
        "system_prompt": system_prompt, "user_prompt_template": user_prompt_template,
        "focus_mode": focus_mode, "created_at": now, "updated_at": now,
    }).to_dict()


def update_template(
    name: str,
    system_prompt: str | None = None,
    user_prompt_template: str | None = None,
    description: str | None = None,
    focus_mode: str | None = None,
) -> dict | None:
    conn = _get_db()
    row = conn.execute("SELECT * FROM templates WHERE name = ?", (name,)).fetchone()
    if not row:
        conn.close()
        return None
    now = _now()
    current = dict(row)
    conn.execute(
        "UPDATE templates SET "
        "system_prompt = ?, user_prompt_template = ?, description = ?, focus_mode = ?, updated_at = ? "
        "WHERE name = ?",
        (
            system_prompt if system_prompt is not None else current["system_prompt"],
            user_prompt_template if user_prompt_template is not None else current["user_prompt_template"],
            description if description is not None else current["description"],
            focus_mode if focus_mode is not None else current["focus_mode"],
            now,
            name,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM templates WHERE name = ?", (name,)).fetchone()
    conn.close()
    return PromptTemplate(dict(row)).to_dict() if row else None


def delete_template(name: str) -> bool:
    conn = _get_db()
    cur = conn.execute("DELETE FROM templates WHERE name = ?", (name,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted
