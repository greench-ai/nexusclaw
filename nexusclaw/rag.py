"""
RAG pipeline — document parsing, chunking, embedding, storage.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import uuid

from nexusclaw.providers import stream_chat
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from pypdf import PdfReader

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# ── Config ────────────────────────────────────────────────────────────────────

QDRANT_HOST = os.environ.get("QDRANT_HOST", "qdrant-nexusclaw")
QDRANT_PORT = 6333
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
EMBEDDING_MODEL = "nomic-embed-text:v1.5"
EMBEDDING_DIMS = 768
COLLECTION_NAME = "nexusclaw_documents"
CHUNK_SIZE = 500  # tokens (approx 750 chars)
CHUNK_OVERLAP = 100  # tokens

# ── Qdrant client ─────────────────────────────────────────────────────────────

_qdrant: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        _ensure_collection(_qdrant)
    return _qdrant


def _ensure_collection(client: QdrantClient):
    """Create collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIMS, distance=Distance.COSINE),
        )


# ── Document parsing ──────────────────────────────────────────────────────────

def parse_pdf(content: bytes) -> str:
    """Extract text from PDF bytes."""
    reader = PdfReader(io.BytesIO(content))
    texts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            texts.append(t)
    return "\n\n".join(texts)


def parse_docx(content: bytes) -> str:
    """Extract text from DOCX bytes."""
    if not HAS_DOCX:
        raise ValueError("python-docx not installed")
    doc = docx.Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def parse_txt(content: bytes) -> str:
    """Extract text from plain text."""
    return content.decode("utf-8", errors="replace")


PARSERS = {
    "application/pdf": parse_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx,
    "text/plain": parse_txt,
    "text/markdown": parse_txt,
}


def parse_file(content: bytes, mime_type: str) -> str:
    """Parse file content to plain text."""
    parser = PARSERS.get(mime_type)
    if not parser:
        # Try plain text as fallback
        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            raise ValueError(f"Unsupported file type: {mime_type}")
    return parser(content)


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split text into overlapping chunks.
    Returns list of {chunk_id, text, start_char, end_char}.
    """
    # Simple token approximation: 1 token ≈ 4 chars
    char_limit = chunk_size * 4
    overlap_chars = overlap * 4

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + char_limit
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk_id = f"chunk_{len(chunks)}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start_char": start,
                "end_char": min(end, text_len),
            })

        # Step forward (with overlap)
        start = start + char_limit - overlap_chars
        if start >= text_len:
            break

    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────

async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts using Ollama nomic-embed-text model."""
    embeddings = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for text in texts:
            resp = await client.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings.append(data["embedding"])
    return embeddings


# ── Storage ────────────────────────────────────────────────────────────────────

def store_document(
    doc_id: str,
    title: str,
    file_type: str,
    chunks: list[dict],
    vectors: list[list[float]],
    metadata: dict | None = None,
) -> dict:
    """Store document chunks + vectors in Qdrant."""
    client = get_qdrant()

    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        point_id = abs(int(hashlib.sha1(f"{doc_id}_{i}".encode()).hexdigest()[:16], 16))
        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "doc_id": doc_id,
                "doc_title": title,
                "file_type": file_type,
                "chunk_id": chunk["chunk_id"],
                "chunk_index": i,
                "text": chunk["text"],
                "metadata": metadata or {},
            },
        ))

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return {
        "doc_id": doc_id,
        "title": title,
        "chunks_stored": len(chunks),
    }


async def search_chunks(query: str, top_k: int = 5, focus_mode: str = "copilot") -> list[dict]:
    """Search for relevant chunks given a query.
    
    focus_mode affects retrieval:
    - copilot: standard retrieval (k=5)
    - academic: +30% boost to documents with "academic" or "arxiv" in title
    - writing: +15% boost to documents with "writing" or "prose" in title
    """
    chunks = await embed_texts([query])
    query_vector = chunks[0]

    client = get_qdrant()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )

    chunks_found = []
    for r in results.points:
        payload = r.payload
        chunks_found.append({
            "text": payload["text"],
            "doc_id": payload["doc_id"],
            "doc_title": payload["doc_title"],
            "chunk_index": payload["chunk_index"],
            "score": r.score,
        })
    return chunks_found


# ── Document metadata ─────────────────────────────────────────────────────────

DOCS_META_PATH = Path.home() / ".nexusclaw" / "rag_documents.json"


def _load_docs_meta() -> dict[str, dict]:
    if DOCS_META_PATH.exists():
        import json
        return json.loads(DOCS_META_PATH.read_text())
    return {}


def _save_docs_meta(meta: dict[str, dict]):
    DOCS_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    import json
    DOCS_META_PATH.write_text(json.dumps(meta, indent=2))


def register_document(doc_id: str, title: str, file_type: str, chunk_count: int, metadata: dict | None = None):
    meta = _load_docs_meta()
    meta[doc_id] = {
        "doc_id": doc_id,
        "title": title,
        "file_type": file_type,
        "chunk_count": chunk_count,
        "uploaded_at": datetime.utcnow().isoformat(),
        "metadata": metadata or {},
    }
    _save_docs_meta(meta)


def list_documents() -> list[dict]:
    meta = _load_docs_meta()
    return list(meta.values())


def delete_document(doc_id: str) -> bool:
    """Delete document chunks from Qdrant and remove metadata."""
    client = get_qdrant()

    # Delete by filter — all chunks with this doc_id
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )

    meta = _load_docs_meta()
    if doc_id in meta:
        del meta[doc_id]
        _save_docs_meta(meta)
        return True
    return False


# ── Citation Fact-Check ───────────────────────────────────────────────────────

async def verify_claim(claim: str, chunks: list[dict]) -> dict:
    """
    Verify a textual claim against retrieved source chunks.
    Returns: { verdict: "verified" | "unsupported" | "contradicted", confidence: float, summary: str }
    """
    if not chunks:
        return {"verdict": "unsupported", "confidence": 0.0, "summary": "No source chunks provided."}

    def _source_text(i, c):
        if hasattr(c, 'model_dump'):
            d = c.model_dump()
        elif hasattr(c, 'dict'):
            d = c.dict()
        else:
            d = c
        return f"[Source {i+1}: {d.get('doc_title', 'unknown')}]\n{d.get('text', '')}"

    sources_text = "\n\n".join(
        _source_text(i, c) for i, c in enumerate(chunks)
    )

    prompt = f"""You are a fact-checker. Given a claim and a set of source documents, determine if the claim is:
- VERIFIED: the source documents fully support the claim
- UNSUPPORTED: the source documents do not contain enough information to verify the claim
- CONTRADICTED: the source documents directly contradict the claim

Respond with ONLY this JSON format (no markdown, no explanation outside JSON):
{{"verdict": "verified|unsupported|contradicted", "confidence": 0.0-1.0, "summary": "2-3 sentence explanation"}}

---
CLAIM: {claim}
---
SOURCES:
{sources_text}
---
VERDICT:"""

    from nexusclaw.main import app_state
    messages = [{"role": "user", "content": prompt}]

    try:
        full_response = []
        async for chunk in stream_chat(app_state.config, app_state.config.default_model, messages):
            if chunk["type"] == "token":
                full_response.append(chunk["content"])
        response_text = "".join(full_response)

        # Parse JSON from response
        import json, re
        json_match = re.search(r'\{[^{}]*"verdict"[^{}]*"confidence"[^{}]*"summary"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            verdict = result.get("verdict", "unsupported").lower()
            if verdict not in ("verified", "unsupported", "contradicted"):
                verdict = "unsupported"
            return {
                "verdict": verdict,
                "confidence": float(result.get("confidence", 0.5)),
                "summary": result.get("summary", ""),
            }
    except Exception as e:
        log.warning("citation.verify_failed", error=str(e))

    return {"verdict": "unsupported", "confidence": 0.0, "summary": "Fact-check failed due to an error."}
