"""
NexusClaw API — config + chat.
Direct provider APIs, no LiteLLM.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import structlog
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from nexusclaw.config import (
    NexusClawConfig,
    ProviderConfig,
    get_config_path,
    load_config,
    save_config,
)
from nexusclaw.providers import chat, stream_chat
from nexusclaw import conversations

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1")


# ── Config ────────────────────────────────────────────────────────────────────

class ProviderPayload(BaseModel):
    name: str
    api_key: str | None = None
    base_url: str | None = None
    models: list[str] = []
    enabled: bool = True
    api_mode: str | None = None


class ChatPayload(BaseModel):
    model: str
    message: str


def _sanitize_config(config: NexusClawConfig) -> dict:
    """Config for API response — no actual API keys exposed."""
    providers = {}
    for name, p in config.providers.items():
        providers[name] = {
            "name": p.name,
            "base_url": p.base_url,
            "models": p.models,
            "enabled": p.enabled,
            "api_mode": getattr(p, "api_mode", "openai-chat"),
        }
    return {
        "version": config.version,
        "default_provider": config.default_provider,
        "default_model": config.default_model,
        "providers": providers,
    }


@router.get("/config")
async def get_config():
    from nexusclaw.main import app_state
    return _sanitize_config(app_state.config)


@router.post("/config/provider")
async def add_provider(payload: ProviderPayload):
    """Add or update a provider. Merges with existing config."""
    from nexusclaw.main import app_state

    config = app_state.config
    config_path = get_config_path()

    # Merge with existing provider if it exists
    existing = config.providers.get(payload.name)
    provider = ProviderConfig(
        name=payload.name,
        api_key=payload.api_key if payload.api_key is not None else (existing.api_key if existing else None),
        base_url=payload.base_url if payload.base_url is not None else (existing.base_url if existing else None),
        models=payload.models if payload.models else (existing.models if existing else []),
        enabled=payload.enabled if payload.enabled is not None else (existing.enabled if existing else True),
        api_mode=payload.api_mode if payload.api_mode is not None else (existing.api_mode if existing else "openai-chat"),
    )

    patched = config.model_copy(deep=True)
    patched.providers[payload.name] = provider

    # If this is the first or only provider, set as default
    if not config.providers or len(config.providers) == 0:
        patched.default_provider = payload.name
        if payload.models:
            patched.default_model = f"{payload.name}/{payload.models[0].split('/')[-1]}"

    save_config(patched, config_path)
    reloaded = load_config(config_path)
    app_state.config = reloaded

    log.info("provider.added", name=payload.name, models=payload.models)
    return {"ok": True, "provider": payload.name}


class DetectAPIModeBody(BaseModel):
    base_url: str
    api_key: str | None = None


@router.post("/config/provider/detect")
async def detect_api_mode(body: DetectAPIModeBody):
    """Auto-detect API mode for a given base_url + optional api_key."""
    from nexusclaw.providers import detect_api_mode as _detect
    mode = await _detect(body.base_url, body.api_key)
    return {"api_mode": mode, "base_url": body.base_url}


@router.delete("/config/provider/{name}")
async def delete_provider(name: str):
    """Remove a provider."""
    from nexusclaw.main import app_state

    config = app_state.config
    config_path = get_config_path()

    if name not in config.providers:
        return {"ok": False, "error": f"Provider '{name}' not found"}

    patched = config.model_copy(deep=True)
    del patched.providers[name]

    if patched.default_provider == name:
        patched.default_provider = next(iter(patched.providers), "ollama")
        models = list(patched.providers.values())[0].models if patched.providers else []
        patched.default_model = f"{patched.default_provider}/{models[0].split('/')[-1]}" if models else "ollama/llama3"

    save_config(patched, config_path)
    reloaded = load_config(config_path)
    app_state.config = reloaded

    return {"ok": True}


# ── Chat ─────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat_endpoint(payload: ChatPayload):
    """Non-streaming chat for testing."""
    from nexusclaw.main import app_state

    model = payload.model or app_state.config.default_model
    messages = [{"role": "user", "content": payload.message}]

    result = await chat(app_state.config, model, messages)
    return result


@router.websocket("/stream/{workspace_id}")
async def chat_stream(ws: WebSocket, workspace_id: str):
    """SSE streaming chat. Saves messages to SQLite, auto-titles conversations."""
    await ws.accept()

    try:
        data = await ws.receive_json()
    except WebSocketDisconnect:
        return

    message = data.get("message", "")
    model = data.get("model")
    conversation_id = data.get("conversation_id")
    use_rag = data.get("rag", False)

    from nexusclaw.main import app_state

    if not model:
        model = app_state.config.default_model

    # Auto-create conversation if none provided
    if conversation_id:
        conv = conversations.get_conversation(conversation_id)
        if not conv:
            conversation_id = None

    if not conversation_id:
        conv = conversations.create_conversation()
        conversation_id = conv["id"]

    # Auto-generate title if still "New conversation"
    conv = conversations.get_conversation(conversation_id)
    if conv and conv["title"] == "New conversation" and message.strip():
        title = conversations.generate_title(message)
        conversations.update_conversation_title(conversation_id, title)

    # Save user message
    conversations.add_message(conversation_id, "user", message, model)

    await ws.send_json({"type": "start", "model": model, "conversation_id": conversation_id})

    # Build messages — optionally with RAG context
    messages = [{"role": "user", "content": message}]

    if use_rag:
        try:
            from nexusclaw.rag import search_chunks
            chunks = await search_chunks(message, top_k=5)
            if chunks:
                context_parts = []
                for c in chunks:
                    context_parts.append(
                        f"[Document: {c['doc_title']}]\n{c['text']}"
                    )
                context = "\n\n---\n\n".join(context_parts)
                system_prompt = (
                    "You have access to the following documents. Use them to answer "
                    "the user's question. If the documents don't contain the answer, say so.\n\n"
                    + context
                )
                messages = [{"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}]
        except Exception as e:
            log.warning("rag.context_injection_failed", error=str(e))

    all_content = []

    try:
        async for chunk in stream_chat(app_state.config, model, messages):
            await ws.send_json(chunk)
            if chunk["type"] == "token":
                all_content.append(chunk["content"])
    except Exception as e:
        log.error("chat.stream_error", error=str(e))
        await ws.send_json({"type": "error", "error": str(e)})
        return

    assistant_content = "".join(all_content)

    # Save assistant message
    conversations.add_message(conversation_id, "assistant", assistant_content, model)

    await ws.send_json({
        "type": "done",
        "model": model,
        "content": assistant_content,
        "conversation_id": conversation_id,
    })
