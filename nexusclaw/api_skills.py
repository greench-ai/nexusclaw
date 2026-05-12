"""
Skills API — skill marketplace + formation.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import yaml

router = APIRouter(prefix="/api/v1/skills")

SKILLS_DIR = Path.home() / ".nexusclaw" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)


class InstallSkillBody(BaseModel):
    url: str
    name: str | None = None


class ProposalBody(BaseModel):
    skill_name: str
    description: str
    trigger: str
    content: str


@router.get("/marketplace")
async def list_marketplace_skills():
    """List all installed skills (local SKILL.md files)."""
    skills = []
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        metadata = {}
        description = ""
        if skill_md.exists():
            text = skill_md.read_text()
            # Parse YAML frontmatter
            if text.startswith("---"):
                end = text.find("\n---", 3)
                if end != -1:
                    try:
                        metadata = yaml.safe_load(text[3:end]) or {}
                        description = metadata.get("description", "")
                    except Exception:
                        pass
        skills.append({
            "name": skill_dir.name,
            "description": description,
            "metadata": metadata,
            "installed": True,
            "path": str(skill_dir),
        })
    return skills


@router.post("/marketplace/install")
async def install_skill(body: InstallSkillBody):
    """Install a skill from a remote SKILL.md URL."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(body.url)
            resp.raise_for_status()
            content = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch SKILL.md: {e}")

    # Determine skill name
    skill_name = body.name
    if not skill_name:
        # Try to extract from URL or use a hash
        from urllib.parse import urlparse
        parsed = urlparse(body.url)
        parts = parsed.path.strip("/").split("/")
        skill_name = parts[-1].replace(".md", "") if parts else "skill"

    skill_dir = SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content)

    return {"ok": True, "name": skill_name, "path": str(skill_dir)}


@router.delete("/marketplace/{name}")
async def uninstall_skill(name: str):
    """Remove an installed skill."""
    import shutil
    skill_dir = SKILLS_DIR / name
    if not skill_dir.exists():
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    shutil.rmtree(skill_dir)
    return {"ok": True}


@router.get("/proposals")
async def list_proposals():
    """List all skill formation proposals."""
    # Check if proposals table exists
    PROPOSALS_DB = Path.home() / ".nexusclaw" / "proposals.db"
    import sqlite3
    if not PROPOSALS_DB.exists():
        return []
    conn = sqlite3.connect(PROPOSALS_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM skill_proposals ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/proposals")
async def create_proposal(body: ProposalBody):
    """Submit a new skill formation proposal."""
    import sqlite3, uuid
    PROPOSALS_DB = Path.home() / ".nexusclaw" / "proposals.db"
    conn = sqlite3.connect(PROPOSALS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skill_proposals (
            id TEXT PRIMARY KEY,
            skill_name TEXT NOT NULL,
            description TEXT,
            trigger TEXT,
            content TEXT,
            status TEXT DEFAULT 'proposed',
            created_at TEXT
        )
    """)
    pid = str(uuid.uuid4())[:8]
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO skill_proposals (id, skill_name, description, trigger, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (pid, body.skill_name, body.description, body.trigger, body.content, "proposed", now)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "id": pid}


@router.post("/proposals/{pid}/approve")
async def approve_proposal(pid: str):
    """Approve a proposal — writes SKILL.md and activates skill."""
    import sqlite3
    PROPOSALS_DB = Path.home() / ".nexusclaw" / "proposals.db"
    if not PROPOSALS_DB.exists():
        raise HTTPException(status_code=404, detail="No proposals found")
    conn = sqlite3.connect(PROPOSALS_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM skill_proposals WHERE id = ?", (pid,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")
    if row["status"] != "proposed":
        conn.close()
        raise HTTPException(status_code=400, detail="Proposal already processed")

    # Write SKILL.md
    skill_dir = SKILLS_DIR / row["skill_name"]
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    content = f"""# {row["skill_name"]}

{description}

## Trigger
{row["trigger"]}

## Content
{row["content"]}
"""
    skill_md.write_text(content)

    # Update proposal status
    conn.execute("UPDATE skill_proposals SET status = ? WHERE id = ?", ("approved", pid))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/proposals/{pid}/reject")
async def reject_proposal(pid: str):
    """Reject a proposal."""
    import sqlite3
    PROPOSALS_DB = Path.home() / ".nexusclaw" / "proposals.db"
    if not PROPOSALS_DB.exists():
        raise HTTPException(status_code=404, detail="No proposals found")
    conn = sqlite3.connect(PROPOSALS_DB)
    conn.execute("UPDATE skill_proposals SET status = ? WHERE id = ?", ("rejected", pid))
    conn.commit()
    conn.close()
    return {"ok": True}
