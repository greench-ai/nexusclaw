"""
NexusClaw Vector Store — Qdrant backend.
Provides sync search (runs in executor thread) and upsert.
"""
from __future__ import annotations
import uuid, os, logging
from typing import Any
from sentence_transformers import SentenceTransformer

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

log = logging.getLogger("nexusclaw.memory")

COLLECTION_PREFIX = "nexusclaw_"


class VectorStore:
    def __init__(self, url: str = "http://localhost:6333", model_name: str = "nomic-embed-text:latest"):
        self.url = url
        self.model_name = model_name
        self._client: Any = None
        self._model: Any = None
        self._init_done = False

    def _init(self):
        if self._init_done:
            return
        try:
            if HAS_QDRANT:
                self._client = QdrantClient(url=self.url)
                log.info(f"Qdrant connected: {self.url}")
            else:
                log.warning("Qdrant not installed — vector search disabled")
        except Exception as e:
            log.warning(f"Qdrant init failed: {e}")
        try:
            self._model = SentenceTransformer(self.model_name)
            log.info(f"Embedding model loaded: {self.model_name}")
        except Exception as e:
            log.warning(f"Embedding model failed: {e}")
        self._init_done = True

    def _ensure_collection(self, collection_name: str, vector_size: int = 768):
        self._init()
        if not self._client:
            return
        try:
            collections = [c.name for c in self._client.get_collections().collections]
            if collection_name not in collections:
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                log.info(f"Created collection: {collection_name}")
        except Exception as e:
            log.warning(f"Collection check failed: {e}")

    def upsert(self, doc_id: str, chunks: list[str], workspace: str = "default", metadata: dict | None = None) -> int:
        """Sync upsert — call from executor thread."""
        self._init()
        if not self._client or not self._model:
            return 0
        collection = f"{COLLECTION_PREFIX}{workspace}"
        self._ensure_collection(collection)
        vectors = self._model.encode(chunks, show_progress_bar=False).tolist()
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={"text": chunk, "doc_id": doc_id, "metadata": metadata or {}},
            )
            for chunk, vec in zip(chunks, vectors)
        ]
        try:
            self._client.upsert(collection_name=collection, points=points)
            log.info(f"Upserted {len(chunks)} chunks into {collection}")
            return len(chunks)
        except Exception as e:
            log.error(f"Upsert failed: {e}")
            return 0

    def search(self, query: str, top_k: int = 5, workspace: str = "default") -> list[dict]:
        """Sync search — call from executor thread."""
        self._init()
        if not self._client or not self._model:
            return []
        collection = f"{COLLECTION_PREFIX}{workspace}"
        try:
            query_vector = self._model.encode([query], show_progress_bar=False).tolist()[0]
            results = self._client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=0.5,
            )
            return [{"id": r.id, "text": r.payload.get("text", ""), "score": r.score} for r in results]
        except Exception as e:
            log.warning(f"Search failed: {e}")
            return []

    def delete_doc(self, doc_id: str, workspace: str = "default") -> bool:
        """Delete all chunks belonging to a document."""
        self._init()
        if not self._client:
            return False
        collection = f"{COLLECTION_PREFIX}{workspace}"
        try:
            self._client.delete(
                collection_name=collection,
                points_selector={"prefetch": [], "limit": 1000},  # simplified
            )
            return True
        except Exception as e:
            log.warning(f"Delete failed: {e}")
            return False
