"""
Conversations API — CRUD for conversations + messages.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from nexusclaw.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
    update_conversation_title,
)

router = APIRouter(prefix="/api/v1/conversations")


class CreateConvBody(BaseModel):
    title: str = "New conversation"


class AddMessageBody(BaseModel):
    role: str
    content: str
    model: str | None = None


class UpdateTitleBody(BaseModel):
    title: str


@router.get("")
async def list_convs() -> list[dict[str, Any]]:
    """List all conversations, newest first."""
    return list_conversations()


@router.post("")
async def create_conv(body: CreateConvBody) -> dict[str, Any]:
    """Create a new conversation."""
    return create_conversation(body.title)


@router.get("/{conv_id}")
async def get_conv(conv_id: str) -> dict[str, Any]:
    """Get a single conversation."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("/{conv_id}/messages")
async def get_conv_messages(conv_id: str) -> list[dict[str, Any]]:
    """Get all messages in a conversation."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return get_messages(conv_id)


@router.post("/{conv_id}/messages")
async def post_message(conv_id: str, body: AddMessageBody) -> dict[str, Any]:
    """Add a message to a conversation."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return add_message(conv_id, body.role, body.content, body.model)


@router.patch("/{conv_id}/title")
async def patch_title(conv_id: str, body: UpdateTitleBody) -> dict[str, Any]:
    """Update conversation title."""
    result = update_conversation_title(conv_id, body.title)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/{conv_id}")
async def delete_conv(conv_id: str) -> dict[str, Any]:
    """Delete a conversation and all its messages."""
    deleted = delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}
