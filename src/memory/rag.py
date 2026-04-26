"""
NexusClaw RAG — Retrieval-Augmented Generation over documents
PDF, DOCX, TXT, HTML → chunks → embeddings → Qdrant → Q&A
"""
import os, json, uuid, asyncio
from pathlib import Path
from typing import Optional

class RAGPipeline:
    """
    Full RAG pipeline:
    1. Parse document (PDF, DOCX, TXT, HTML)
    2. Chunk text
    3. Embed chunks
    4. Store in Qdrant
    5. Retrieve relevant chunks
    6. Generate answer with context
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = None
    
    def parse_document(self, file_path: str) -> str:
        """Extract text from any document type."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == ".txt" or ext == ".md":
            return self._parse_txt(file_path)
        elif ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return self._parse_docx(file_path)
        elif ext == ".html":
            return self._parse_html(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _parse_txt(self, path: str) -> str:
        with open(path, "r", errors="ignore") as f:
            return f.read()
    
    def _parse_pdf(self, path: str) -> str:
        try:
            import pymupdf
            doc = pymupdf.open(path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except ImportError:
            return "[PDF parsing requires pymupdf: pip install pymupdf]"
    
    def _parse_docx(self, path: str) -> str:
        try:
            import mammoth
            with open(path, "rb") as f:
                result = mammoth.extract_raw_text(f)
            return result.value
        except ImportError:
            return "[DOCX parsing requires mammoth: pip install mammoth]"
    
    def _parse_html(self, path: str) -> str:
        try:
            from bs4 import BeautifulSoup
            with open(path, "r", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except ImportError:
            return self._parse_txt(path)
    
    def chunk_text(self, text: str) -> list[dict]:
        """Split text into overlapping chunks with metadata."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            if not chunk_words:
                continue
            
            chunk_text = " ".join(chunk_words)
            chunk_id = str(uuid.uuid4())
            
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "word_count": len(chunk_words),
                "char_count": len(chunk_text),
                "start_word": i,
                "end_word": i + len(chunk_words)
            })
        
        return chunks
    
    async def index_document(self, file_path: str, metadata: dict = None) -> dict:
        """Full pipeline: parse → chunk → embed → store."""
        # Parse
        text = self.parse_document(file_path)
        if text.startswith("["):
            return {"status": "error", "message": text}
        
        # Chunk
        chunks = self.chunk_text(text)
        
        # Embed + store (async)
        file_id = str(uuid.uuid4())
        indexed_count = 0
        
        for chunk in chunks:
            # In production: embed with nomic-embed-text via Ollama
            # For now: store as-is
            try:
                from ..memory.vector_store import get_store
                store = get_store()
                store.add(
                    content=chunk["text"],
                    metadata={
                        "file_id": file_id,
                        "chunk_id": chunk["id"],
                        "file_path": file_path,
                        **(metadata or {})
                    }
                )
                indexed_count += 1
            except Exception as e:
                print(f"Index failed for chunk: {e}")
        
        return {
            "file_id": file_id,
            "file_path": file_path,
            "chunks_total": len(chunks),
            "chunks_indexed": indexed_count,
            "status": "indexed"
        }
    
    async def query(self, question: str, file_ids: list = None, top_k: int = 5) -> dict:
        """Query indexed documents."""
        try:
            from ..memory.vector_store import get_store
            store = get_store()
            
            # Search
            results = store.search(
                query=question,
                limit=top_k,
                filter_metadata={"file_id": {"$in": file_ids}} if file_ids else None
            )
            
            if not results:
                return {"answer": "No relevant documents found.", "sources": []}
            
            # Build context
            context = "\n\n".join([
                f"[Source {i+1}]: {r['content']}"
                for i, r in enumerate(results)
            ])
            
            # Generate answer (in production: use LLM with context)
            answer = f"Based on {len(results)} relevant document(s):\n\n{context[:500]}..."
            
            return {
                "answer": answer,
                "sources": [
                    {"content": r["content"][:200] + "...", "score": r["score"], "file": r["metadata"].get("file_path", "?")}
                    for r in results
                ]
            }
        except Exception as e:
            return {"answer": f"Query error: {e}", "sources": []}

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NexusClaw RAG Pipeline")
    parser.add_argument("action", choices=["index", "query"], help="index a file or query documents")
    parser.add_argument("--file", help="file to index")
    parser.add_argument("--question", help="question to answer")
    parser.add_argument("--top-k", type=int, default=5, help="number of results")
    args = parser.parse_args()
    
    rag = RAGPipeline()
    
    if args.action == "index":
        if not args.file:
            print("Error: --file required for index")
        else:
            result = asyncio.run(rag.index_document(args.file))
            print(json.dumps(result, indent=2))
    
    elif args.action == "query":
        if not args.question:
            print("Error: --question required for query")
        else:
            result = asyncio.run(rag.query(args.question, top_k=args.top_k))
            print(json.dumps(result, indent=2))
