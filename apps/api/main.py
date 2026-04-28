"""
NexusClaw API Server v1.0
FastAPI — REST + WebSocket streaming, JWT auth, chat sessions, files, RAG, autonomy.
"""
from __future__ import annotations

import os, sys, json, uuid, asyncio, logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, AsyncIterator
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt, bcrypt, time

# ─── Setup paths ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent   # nexusclaw/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ─── Config ───────────────────────────────────────────────────────────────────
CONFIG_PATH = Path(os.environ.get("NEXUS_CONFIG", str(Path.home() / ".nexusclaw" / "config.json")))
_config: dict | None = None

def load_config() -> dict:
    global _config
    if _config is None:
        if CONFIG_PATH.exists():
            _config = json.loads(CONFIG_PATH.read_text())
        else:
            _config = {
                "api": {"port": 8080, "secret": "dev-secret-change-me"},
                "providers": {
                    "openai":    {"api_key": os.environ.get("OPENAI_API_KEY", "")},
                    "anthropic": {"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
                    "openrouter":{"api_key": os.environ.get("OPENROUTER_API_KEY", "")},
                    "perplexity":{"api_key": os.environ.get("PERPLEXITY_API_KEY", "")},
                    "ollama":    {"url": os.environ.get("OLLAMA_URL", "http://localhost:11434")},
                },
                "memory": {
                    "vector_db": "qdrant",
                    "qdrant_url": os.environ.get("QDRANT_URL", "http://localhost:6333"),
                    "embedding_model": "nomic-embed-text",
                },
            }
    return _config

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
log = logging.getLogger("nexusclaw.api")

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="NexusClaw API", version="1.0.0", description="Your framework. Your rules.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Security ─────────────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)
_executor = ThreadPoolExecutor(max_workers=4)

def _secret() -> str:
    return load_config()["api"].get("secret", "dev-secret")

def create_token(user_id: str, expires_h: int = 24) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=expires_h),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if not cred:
        raise HTTPException(401, "Missing auth token")
    user = verify_token(cred.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

# ─── Stores ───────────────────────────────────────────────────────────────────
# In-memory stores (replace with SQLite/Postgres in production)
users_db: dict[str, dict] = {}
sessions_db: dict[str, dict] = {}
connections: dict[str, list[WebSocket]] = {}
files_db: dict[str, dict] = {}
goals_db: dict[str, dict] = {}
skills_db: dict[str, dict] = {}

# ─── Pydantic Models ───────────────────────────────────────────────────────────
class AuthRegister(BaseModel):
    email: str; password: str; display_name: str = "User"

class AuthLogin(BaseModel):
    email: str; password: str

class ChatReq(BaseModel):
    session_id: Optional[str] = None
    message: str
    provider: str = "openrouter"
    model: str = "qwen/qwen3.5-plus"
    stream: bool = True
    use_rag: bool = True
    citations: bool = False

class GoalReq(BaseModel):
    title: str
    objective: str
    constraints: dict = Field(default_factory=dict)
    auto_approve: bool = False

class SkillRunReq(BaseModel):
    skill_name: str
    params: dict = Field(default_factory=dict)

class MemoryQueryReq(BaseModel):
    query: str
    top_k: int = 5
    workspace: str = "default"

class FileUploadResp(BaseModel):
    file_id: str; filename: str; chunks: int; status: str

# ─── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    cfg = load_config()
    return {
        "status": "ok",
        "version": "1.0.0",
        "providers": {
            name: bool(data.get("api_key") or data.get("url"))
            for name, data in cfg.get("providers", {}).items()
        },
        "memory": cfg.get("memory", {}).get("vector_db", "none"),
    }

# ─── Auth ─────────────────────────────────────────────────────────────────────
@app.post("/auth/register")
async def register(body: AuthRegister):
    if body.email in users_db:
        raise HTTPException(400, "Email already registered")
    uid = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    users_db[uid] = {"id": uid, "email": body.email, "name": body.display_name, "password": pw_hash}
    token = create_token(uid)
    return {"token": token, "user": {"id": uid, "email": body.email, "name": body.display_name}}

@app.post("/auth/login")
async def login(body: AuthLogin):
    for uid, user in users_db.items():
        if user["email"] == body.email and bcrypt.checkpw(body.password.encode(), user["password"].encode()):
            return {"token": create_token(uid), "user": {"id": uid, "email": user["email"], "name": user["name"]}}
    raise HTTPException(401, "Invalid credentials")

# ─── Sessions ─────────────────────────────────────────────────────────────────
@app.get("/sessions")
async def list_sessions(user: str = Depends(get_current_user)):
    return [
        {"id": sid, "title": s.get("title", "Untitled"), "updated_at": s.get("updated_at")}
        for sid, s in sessions_db.items()
        if s.get("user_id") == user
    ]

@app.post("/sessions")
async def create_session(user: str = Depends(get_current_user)):
    sid = str(uuid.uuid4())
    sessions_db[sid] = {"id": sid, "user_id": user, "title": "New Chat", "messages": [], "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()}
    return {"id": sid, "title": "New Chat"}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str, user: str = Depends(get_current_user)):
    if session_id not in sessions_db:
        raise HTTPException(404, "Session not found")
    return sessions_db[session_id]

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: str = Depends(get_current_user)):
    if session_id in sessions_db:
        del sessions_db[session_id]
    return {"ok": True}

# ─── Provider dispatch ──────────────────────────────────────────────────────────
async def _stream_openai(messages: list, model: str, api_key: str, cfg: dict) -> AsyncIterator[str]:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY",""))
        stream = await client.chat.completions.create(
            model=model, messages=messages, stream=True,
            temperature=0.7, max_tokens=8192,
        )
        async for chunk in stream:
            if chunk.choices and (delta := chunk.choices[0].delta.content):
                yield delta
    except Exception as e:
        yield f"[OpenAI error: {e}]"

async def _stream_anthropic(messages: list, model: str, api_key: str, cfg: dict) -> AsyncIterator[str]:
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY",""))
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user_msgs = [m for m in messages if m.get("role") != "system"]
        async with client.messages.stream(
            model=model or "claude-3-5-sonnet-20241022",
            system=system,
            messages=user_msgs,
            max_tokens=8192,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"[Anthropic error: {e}]"

async def _stream_ollama(messages: list, model: str, api_key: str, cfg: dict) -> AsyncIterator[str]:
    try:
        url = cfg.get("ollama", {}).get("url", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", f"{url}/api/chat",
                json={"model": model or "llama3.2", "messages": messages, "stream": True}
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if content := data.get("message", {}).get("content"):
                                yield content
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        yield f"[Ollama error: {e}]"

async def _stream_openrouter(messages: list, model: str, api_key: str, cfg: dict) -> AsyncIterator[str]:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY",""),
        )
        stream = await client.chat.completions.create(
            model=model or "qwen/qwen3.5-plus",
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=8192,
        )
        async for chunk in stream:
            if chunk.choices and (delta := chunk.choices[0].delta.content):
                yield delta
    except Exception as e:
        yield f"[Openrouter error: {e}]"

PROVIDER_STREAMERS = {
    "openai":     _stream_openai,
    "anthropic":  _stream_anthropic,
    "ollama":     _stream_ollama,
    "openrouter": _stream_openrouter,
}

# ─── Chat ─────────────────────────────────────────────────────────────────────
@app.post("/chat/stream")
async def chat_stream(body: ChatReq, user: str = Depends(get_current_user)):
    cfg = load_config()
    sid = body.session_id or str(uuid.uuid4())
    provider = body.provider
    streamer = PROVIDER_STREAMERS.get(provider)

    if not streamer:
        return JSONResponse({"error": f"Unknown provider: {provider}"}, status_code=400)

    api_key = cfg.get("providers", {}).get(provider, {}).get("api_key", "")

    # Build messages
    soul = _get_soul(user)
    messages = [
        {"role": "system", "content": soul},
        *[m for m in _get_session_messages(sid)],
        {"role": "user", "content": body.message},
    ]

    # RAG context
    if body.use_rag:
        context = await _rag_query(body.message, user)
        if context:
            messages[0]["content"] = soul + f"\n\n[Relevant context from knowledge base]\n{context}"

    # Save user message
    _append_message(sid, user, "user", body.message)

    async def event_generator():
        full = ""
        async for token in streamer(messages, body.model, api_key, cfg):
            full += token
            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
        yield f"data: {json.dumps({'token': '', 'done': True, 'full': full})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Session-Id": sid},
    )

@app.post("/chat")
async def chat_no_stream(body: ChatReq, user: str = Depends(get_current_user)):
    cfg = load_config()
    sid = body.session_id or str(uuid.uuid4())
    streamer = PROVIDER_STREAMERS.get(body.provider)
    if not streamer:
        raise HTTPException(400, f"Unknown provider: {body.provider}")

    api_key = cfg.get("providers", {}).get(body.provider, {}).get("api_key", "")
    soul = _get_soul(user)
    messages = [
        {"role": "system", "content": soul},
        *[m for m in _get_session_messages(sid)],
        {"role": "user", "content": body.message},
    ]

    if body.use_rag:
        context = await _rag_query(body.message, user)
        if context:
            messages[0]["content"] = soul + f"\n\n[Context]\n{context}"

    _append_message(sid, user, "user", body.message)

    # Collect all tokens
    full = ""
    async for token in streamer(messages, body.model, api_key, cfg):
        full += token

    _append_message(sid, user, "assistant", full)
    return {"session_id": sid, "response": full}

# ─── RAG / Memory ────────────────────────────────────────────────────────────────
async def _rag_query(query: str, user: str, top_k: int = 5) -> str:
    """Query vector DB and return context string."""
    try:
        from src.memory.vector_store import VectorStore
        cfg = load_config()
        store = VectorStore(cfg.get("memory", {}).get("qdrant_url", "http://localhost:6333"))
        results = await asyncio.get_event_loop().run_in_executor(
            _executor, lambda: store.search(query, top_k=top_k, workspace=user)
        )
        if not results:
            return ""
        return "\n".join([f"[{r['score']:.2f}] {r['text']}" for r in results])
    except Exception as e:
        log.warning(f"RAG query failed: {e}")
        return ""

# ─── Files / RAG Upload ────────────────────────────────────────────────────────
@app.post("/files/upload", response_model=FileUploadResp)
async def upload_file(file: UploadFile = File(...), user: str = Depends(get_current_user)):
    fid = str(uuid.uuid4())
    files_db[fid] = {"id": fid, "filename": file.filename, "user": user, "status": "indexing"}
    asyncio.create_task(_index_file(fid, file, user))
    return FileUploadResp(file_id=fid, filename=file.filename, chunks=0, status="indexing")

async def _index_file(fid: str, file: UploadFile, user: str):
    """Background: parse file, chunk, embed, store in Qdrant."""
    try:
        from src.memory.vector_store import VectorStore
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        chunks = [text[i:i+500] for i in range(0, len(text), 400)]
        cfg = load_config()
        store = VectorStore(cfg.get("memory", {}).get("qdrant_url", "http://localhost:6333"))
        await asyncio.get_event_loop().run_in_executor(
            _executor, lambda: store.upsert(fid, chunks, user)
        )
        files_db[fid]["status"] = "ready"
        files_db[fid]["chunks"] = len(chunks)
        log.info(f"Indexed {file.filename}: {len(chunks)} chunks")
    except Exception as e:
        files_db[fid]["status"] = f"error: {e}"

# ─── Autonomy / Goals ───────────────────────────────────────────────────────────
@app.post("/autonomy/goals")
async def create_goal(body: GoalReq, user: str = Depends(get_current_user)):
    gid = str(uuid.uuid4())
    goals_db[gid] = {
        "id": gid, "title": body.title, "objective": body.objective,
        "constraints": body.constraints, "auto_approve": body.auto_approve,
        "user": user, "status": "pending", "tasks": [], "created_at": datetime.utcnow().isoformat(),
    }
    return {"id": gid, "status": "pending"}

@app.get("/autonomy/goals")
async def list_goals(user: str = Depends(get_current_user)):
    return [g for g in goals_db.values() if g.get("user") == user]

@app.delete("/autonomy/goals/{gid}")
async def delete_goal(gid: str, user: str = Depends(get_current_user)):
    if gid in goals_db and goals_db[gid].get("user") == user:
        goals_db[gid]["status"] = "cancelled"
    return {"ok": True}

@app.post("/autonomy/kill")
async def kill_all(user: str = Depends(get_current_user)):
    for goal in goals_db.values():
        if goal.get("user") == user and goal.get("status") in ("pending", "running"):
            goal["status"] = "killed"
    return {"ok": True, "killed": len([g for g in goals_db.values() if g.get("user") == user and g.get("status") == "killed"])}

# ─── Skills ───────────────────────────────────────────────────────────────────
@app.get("/skills")
async def list_skills():
    from pathlib import Path
    skills_dir = ROOT / "skills"
    result = []
    for d in skills_dir.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            result.append({
                "name": d.name,
                "description": (d / "SKILL.md").read_text().split("\n")[0].lstrip("# ").strip(),
            })
    return result

@app.post("/skills/run")
async def run_skill(body: SkillRunReq, user: str = Depends(get_current_user)):
    from pathlib import Path
    skill_path = ROOT / "skills" / body.skill_name / "SKILL.md"
    if not skill_path.exists():
        raise HTTPException(404, f"Skill not found: {body.skill_name}")
    # Skill execution is a placeholder — full implementation uses autonomy engine
    return {"skill": body.skill_name, "params": body.params, "status": "placeholder"}

# ─── Soul ──────────────────────────────────────────────────────────────────────
def _get_soul(user: str) -> str:
    soul_path = Path.home() / ".nexusclaw" / "souls" / f"{user}.md"
    if soul_path.exists():
        return soul_path.read_text()
    cfg = load_config()
    template = cfg.get("soul", {}).get("template", "assistant")
    defaults = {
        "assistant": "You are NexusClaw, a helpful AI assistant.",
        "coder": "You are NexusClaw, an expert programmer. Write clean, efficient code.",
        "researcher": "You are NexusClaw, a thorough researcher. Be precise and cite sources.",
    }
    return defaults.get(template, defaults["assistant"])

def _get_session_messages(sid: str) -> list:
    return sessions_db.get(sid, {}).get("messages", [])

def _append_message(sid: str, user: str, role: str, content: str):
    if sid not in sessions_db:
        sessions_db[sid] = {"id": sid, "user_id": user, "title": content[:40], "messages": []}
    sessions_db[sid]["messages"].append({"role": role, "content": content, "ts": datetime.utcnow().isoformat()})
    sessions_db[sid]["updated_at"] = datetime.utcnow().isoformat()
    if len(sessions_db[sid]["messages"]) == 1:
        sessions_db[sid]["title"] = content[:40]

# ─── SSE WebSocket ─────────────────────────────────────────────────────────────
@app.websocket("/ws/{session_id}")
async def websocket_chat(ws: WebSocket, session_id: str):
    await ws.accept()
    if session_id not in connections:
        connections[session_id] = []
    connections[session_id].append(ws)
    try:
        while True:
            data = await ws.receive_text()
            req = json.loads(data)
            # Broadcast to all connections in this session
            for client in connections[session_id]:
                if client != ws:
                    await client.send_json({"type": "message", "data": req})
    except WebSocketDisconnect:
        if session_id in connections:
            connections[session_id] = [c for c in connections[session_id] if c != ws]

# ─── httpx import (lazy) ───────────────────────────────────────────────────────
import httpx

if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    port = cfg.get("api", {}).get("port", 8080)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
