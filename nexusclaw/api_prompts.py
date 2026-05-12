"""
Prompt Templates API — CRUD for prompt templates.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from nexusclaw.prompts import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    update_template,
)

router = APIRouter(prefix="/api/v1/prompts")


class CreatePromptBody(BaseModel):
    name: str
    system_prompt: str
    user_prompt_template: str = ""
    description: str = ""
    focus_mode: str = "copilot"


class UpdatePromptBody(BaseModel):
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    description: str | None = None
    focus_mode: str | None = None


@router.get("")
async def list_prompts():
    """List all prompt templates."""
    return {"templates": list_templates()}


@router.get("/{name}")
async def get_prompt(name: str):
    """Get a single template by name."""
    tpl = get_template(name)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return tpl


@router.post("")
async def create_prompt(body: CreatePromptBody):
    """Create a new prompt template."""
    existing = get_template(body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Template '{body.name}' already exists")
    try:
        tpl = create_template(
            name=body.name,
            system_prompt=body.system_prompt,
            user_prompt_template=body.user_prompt_template,
            description=body.description,
            focus_mode=body.focus_mode,
        )
        return tpl
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{name}")
async def update_prompt(name: str, body: UpdatePromptBody):
    """Update a prompt template."""
    tpl = update_template(
        name=name,
        system_prompt=body.system_prompt,
        user_prompt_template=body.user_prompt_template,
        description=body.description,
        focus_mode=body.focus_mode,
    )
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return tpl


@router.delete("/{name}")
async def delete_prompt(name: str):
    """Delete a prompt template."""
    deleted = delete_template(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return {"ok": True}
