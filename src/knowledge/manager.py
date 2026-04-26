"""NexusClaw Knowledge Base Manager — Document management and RAG."""
import os, json, uuid, asyncio
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Document:
    id: str; title: str; filename: str; file_path: str; file_type: str
    size_bytes: int; chunks_count: int; indexed: bool; status: str
    created_at: str; indexed_at: str = ""; tags: list = field(default_factory=list)
    workspace: str = "default"

class KnowledgeBase:
    def __init__(self, workspace: str = "default"):
        self.workspace = workspace
        self.base_dir = Path(os.environ.get("NEXUS_WORKSPACE", "~/.nexusclaw")).expanduser()
        self.kb_dir = self.base_dir / "knowledge" / workspace
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.kb_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file) as f:
                data = json.load(f)
                self.documents = {d["id"]: Document(**d) for d in data.get("documents", [])}
        else:
            self.documents = {}
    
    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump({"workspace": self.workspace, "updated_at": datetime.utcnow().isoformat()+"Z",
                "documents": [d.__dict__ for d in self.documents.values()]}, f, indent=2)
    
    def add(self, file_path: str, title: str = None, tags: list = None) -> Document:
        path = Path(file_path)
        doc = Document(id=str(uuid.uuid4()), title=title or path.stem, filename=path.name,
            file_path=str(path.absolute()), file_type=path.suffix.lower().lstrip("."),
            size_bytes=path.stat().st_size, chunks_count=0, indexed=False, status="pending",
            created_at=datetime.utcnow().isoformat()+"Z", tags=tags or [], workspace=self.workspace)
        self.documents[doc.id] = doc; self._save_index(); return doc
    
    async def index(self, doc_id: str) -> Document:
        doc = self.documents.get(doc_id)
        if not doc: raise ValueError(f"Document {doc_id} not found")
        doc.status = "indexing"; self._save_index()
        try:
            from ..memory.rag import RAGPipeline
            rag = RAGPipeline()
            result = await rag.index_document(doc.file_path, metadata={"doc_id": doc_id, "title": doc.title, "workspace": self.workspace})
            doc.chunks_count = result.get("chunks_indexed", 0); doc.indexed = True
            doc.status = "indexed"; doc.indexed_at = datetime.utcnow().isoformat()+"Z"
        except Exception as e:
            doc.status = "error"
        self._save_index(); return doc
    
    async def index_all(self) -> dict:
        pending = [d for d in self.documents.values() if d.status == "pending"]
        for i, doc in enumerate(pending):
            print(f"[{i+1}/{len(pending)}] {doc.title}")
            try: await self.index(doc.id)
            except Exception as e: print(f"  Error: {e}")
        return {"total": len(pending), "indexed": len([d for d in pending if d.indexed])}
    
    def search(self, query: str, top_k: int = 5) -> list:
        try:
            from ..memory.vector_store import get_store
            return get_store().search(query, limit=top_k)
        except: return []
    
    def list_all(self): return sorted(self.documents.values(), key=lambda d: d.created_at, reverse=True)
    
    def stats(self) -> dict:
        docs = list(self.documents.values())
        return {"total": len(docs), "indexed": len([d for d in docs if d.indexed]),
                "pending": len([d for d in docs if d.status=="pending"])}
