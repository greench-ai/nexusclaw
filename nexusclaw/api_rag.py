"""
RAG API — document upload, search, and chat with context.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import structlog
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from nexusclaw.rag import (
    parse_file,
    chunk_text,
    embed_texts,
    store_document,
    register_document,
    list_documents,
    delete_document,
    search_chunks,
)

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/rag")


# ── Models ────────────────────────────────────────────────────────────────────

class ChatWithRAGBody(BaseModel):
    message: str
    model: str
    conversation_id: str | None = None
    top_k: int = 5


class SearchBody(BaseModel):
    query: str
    top_k: int = 5


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document, parse it, chunk it, embed it, and store in Qdrant."""
    content = await file.read()

    # Parse
    try:
        text = parse_file(content, file.content_type or "application/octet-stream")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Document is empty after parsing")

    # Chunk
    chunks = chunk_text(text)

    # Generate doc ID from content hash
    doc_id = hashlib.sha256(content[:8192]).hexdigest()[:12]

    # Embed chunks
    try:
        texts = [c["text"] for c in chunks]
        vectors = await embed_texts(texts)
    except Exception as e:
        log.error("rag.embedding_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Embedding failed (is Ollama running?): {e}")

    # Store
    try:
        title = Path(file.filename or "untitled").stem
        result = store_document(
            doc_id=doc_id,
            title=title,
            file_type=file.content_type or "unknown",
            chunks=chunks,
            vectors=vectors,
        )
    except Exception as e:
        log.error("rag.storage_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store in Qdrant: {e}")

    # Register metadata
    register_document(doc_id, title, file.content_type or "unknown", len(chunks))

    log.info("rag.document_uploaded", doc_id=doc_id, title=title, chunks=len(chunks))

    return {
        "ok": True,
        "doc_id": doc_id,
        "title": title,
        "chunks_stored": len(chunks),
        "text_length": len(text),
    }


# ── List / Delete ─────────────────────────────────────────────────────────────

@router.get("/documents")
async def get_documents():
    """List all indexed documents."""
    return {"documents": list_documents()}


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str):
    """Delete a document and all its chunks from Qdrant."""
    deleted = delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    log.info("rag.document_deleted", doc_id=doc_id)
    return {"ok": True}


# ── Search ────────────────────────────────────────────────────────────────────

@router.post("/search")
async def search_documents(body: SearchBody):
    """Semantic search across all indexed documents."""
    try:
        results = await search_chunks(body.query, top_k=body.top_k)
    except Exception as e:
        log.error("rag.search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
    return {"results": results, "query": body.query}


# ── Chat with RAG ─────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat_with_rag(body: ChatWithRAGBody):
    """
    Chat with RAG context. Retrieves relevant chunks, builds context,
    sends to LLM, and streams response.
    """
    from nexusclaw.main import app_state
    from nexusclaw.providers import stream_chat

    # Retrieve relevant chunks
    try:
        chunks = await search_chunks(body.message, top_k=body.top_k)
    except Exception as e:
        chunks = []
        log.warning("rag.retrieval_failed", error=str(e))

    # Build context
    if chunks:
        context_parts = []
        for i, c in enumerate(chunks):
            context_parts.append(
                f"[Document: {c['doc_title']}]\n"
                f"{c['text']}"
            )
        context = "\n\n---\n\n".join(context_parts)
        system_prompt = (
            "You have access to the following documents. Use them to answer the user's question. "
            "If the documents don't contain the answer, say so.\n\n"
            f"{context}"
        )
    else:
        system_prompt = "You are a helpful AI assistant."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": body.message},
    ]

    all_content = []

    try:
        async for chunk in stream_chat(app_state.config, body.model, messages):
            yield chunk
            if chunk["type"] == "token":
                all_content.append(chunk["content"])
    except Exception as e:
        log.error("rag.chat_failed", error=str(e))
        yield {"type": "error", "error": str(e)}
