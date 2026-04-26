"""
NexusClaw API Server v0.3
FastAPI + WebSocket streaming, JWT auth, chat sessions, file upload, RAG, autonomous goals.
"""
import asyncio, json, uuid, jwt, datetime, os
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="NexusClaw API", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# === Stores ===
users_db, sessions_db, files_db, goals_db = {}, {}, {}, {}
connections = {}

SECRET = os.environ.get("NEXUS_SECRET", "nexusclaw-dev-change-in-production")
ALLOWED_PROVIDERS = {"ollama": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
                     "openai": os.environ.get("OPENAI_API_KEY", ""),
                     "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
                     "minimaxi": os.environ.get("MINIMAXI_API_KEY", "")}

# === Models ===
class AuthReq(BaseModel): email: str; password: str; displayName: str = "User"
class LoginReq(BaseModel): email: str; password: str
class ChatReq(BaseModel): sessionId: Optional[str] = None; message: str; provider: str = "ollama"; model: str = "llama3.2"; citations: bool = True
class GoalReq(BaseModel): title: str; objective: str; constraints: dict = {}

# === WebSocket ===
class ConnectionManager:
    def __init__(self): self.active: dict[str, list[WebSocket]] = {}
    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        if session_id not in self.active: self.active[session_id] = []
        self.active[session_id].append(ws)
    def disconnect(self, ws: WebSocket, session_id: str):
        if session_id in self.active: self.active[session_id] = [w for w in self.active[session_id] if w != ws]
    async def broadcast(self, session_id: str, data: dict):
        if session_id in self.active:
            for ws in self.active[session_id]:
                try: await ws.send_json(data)
                except: pass

ws_manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws_manager.connect(ws, session_id)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "chat":
                response = await generate_response(msg["content"], msg.get("provider","ollama"), msg.get("model","llama3.2"))
                await ws.send_json({"type": "chunk", "content": response})
                await ws.send_json({"type": "done"})
            elif msg.get("type") == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws, session_id)

# === Auth ===
def get_user(authorization: str = "") -> dict:
    if not authorization.startswith("Bearer "): raise HTTPException(401, "Missing token")
    try:
        payload = jwt.decode(authorization[7:], SECRET, algorithms=["HS256"])
        return users_db[payload["email"]]
    except: raise HTTPException(401, "Invalid token")

@app.post("/health") 
def health(): return {"ok": True, "service": "nexusclaw-api", "version": "0.3.0"}

@app.post("/v1/auth/register")
def register(req: AuthReq):
    if req.email in users_db: raise HTTPException(400, "User exists")
    user = {"id": str(uuid.uuid4()), "email": req.email, "passwordHash": req.password,
            "displayName": req.displayName, "workspaceId": str(uuid.uuid4()),
            "createdAt": datetime.datetime.utcnow().isoformat()}
    users_db[req.email] = user
    token = jwt.encode({"sub": user["id"], "email": req.email}, SECRET, algorithm="HS256")
    return {"token": token, "user": {k:v for k,v in user.items() if k!="passwordHash"}, "workspace": {"id": user["workspaceId"]}}

@app.post("/v1/auth/login")
def login(req: LoginReq):
    user = users_db.get(req.email)
    if not user or user["passwordHash"] != req.password: raise HTTPException(401, "Invalid")
    token = jwt.encode({"sub": user["id"], "email": req.email}, SECRET, algorithm="HS256")
    return {"token": token, "user": {k:v for k,v in user.items() if k!="passwordHash"}, "workspace": {"id": user["workspaceId"]}}

# === Chat ===
@app.post("/v1/chat/sessions")
def create_session(user=Depends(get_user), title: str = "New Session"):
    session = {"id": str(uuid.uuid4()), "userId": user["id"], "title": title, "messages": [], "createdAt": datetime.datetime.utcnow().isoformat()}
    sessions_db[session["id"]] = session
    return session

@app.get("/v1/chat/sessions")
def list_sessions(user=Depends(get_user)):
    return [s for s in sessions_db.values() if s["userId"] == user["id"]]

@app.post("/v1/chat/answer/stream")
async def stream_chat(req: ChatReq, user=Depends(get_user)):
    """SSE streaming response."""
    session = sessions_db.get(req.sessionId)
    messages = session["messages"] if session else []
    messages.append({"role": "user", "content": req.message})
    
    async def generate():
        try:
            async for chunk in stream_from_provider(req.provider, req.model, messages):
                yield f"data: {json.dumps({'type':'chunk','content':chunk})}\n\n"
            messages.append({"role": "assistant", "content": "[full response]"})
            if session: session["messages"] = messages[-20:]
            yield f"data: {json.dumps({'type':'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','content':str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

async def stream_from_provider(provider: str, model: str, messages: list) -> AsyncIterator[str]:
    if provider == "ollama":
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {"model": model, "messages": messages, "stream": True}
            async with session.post(f"{ALLOWED_PROVIDERS['ollama']}/api/chat", json=payload) as resp:
                async for line in resp.content:
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "content" in chunk.get("message", {}):
                                yield chunk["message"]["content"]
                        except: pass
    elif provider == "openai":
        import aiohttp
        api_key = ALLOWED_PROVIDERS.get("openai", "")
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "messages": messages, "stream": True}
            async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: ") and text != "data: [DONE]":
                            try:
                                c = json.loads(text[6:])
                                if delta := c.get("choices", [{}])[0].get("delta", {}).get("content"):
                                    yield delta
                            except: pass
    elif provider == "minimaxi":
        import aiohttp
        api_key = ALLOWED_PROVIDERS.get("minimaxi", "")
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "messages": messages, "stream": True}
            async with session.post("https://api.minimax.io/v1/text/chatcompletion_v2", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if line:
                        text = line.decode().strip()
                        if text.startswith("data: ") and text != "data: [DONE]":
                            try:
                                c = json.loads(text[6:])
                                if delta := c.get("choices", [{}])[0].get("delta", {}).get("content"):
                                    yield delta
                            except: pass
    else:
        yield f"[Provider '{provider}' not configured. Set {provider.upper()}_API_KEY environment variable.]"

async def generate_response(message: str, provider: str, model: str) -> str:
    result = ""
    async for chunk in stream_from_provider(provider, model, [{"role": "user", "content": message}]):
        result += chunk
    return result

# === Files ===
@app.post("/v1/files/upload")
async def upload_file(file: UploadFile = File(...), user=Depends(get_user)):
    content = await file.read()
    file_id = str(uuid.uuid4())
    files_db[file_id] = {"fileId": file_id, "userId": user["id"], "filename": file.filename,
                         "size": len(content), "status": "queued",
                         "createdAt": datetime.datetime.utcnow().isoformat()}
    asyncio.create_task(index_file(file_id, content, file.filename))
    return {"ok": True, "fileId": file_id, "status": "queued"}

async def index_file(file_id: str, content: bytes, filename: str):
    await asyncio.sleep(1)  # Simulate async processing
    if file_id in files_db:
        files_db[file_id]["status"] = "indexed"
        files_db[file_id]["chunks"] = len(content) // 500

@app.get("/v1/files")
def list_files(user=Depends(get_user)):
    return [f for f in files_db.values() if f["userId"] == user["id"]]

# === Autonomous Goals ===
@app.post("/v1/autonomy/goals")
def create_goal(req: GoalReq, user=Depends(get_user)):
    goal = {"id": str(uuid.uuid4()), "workspaceId": user["workspaceId"], "creatorUserId": user["id"],
            "title": req.title, "objective": req.objective, "constraints": req.constraints,
            "status": "queued", "tasks": [], "events": [], "approvals": [],
            "createdAt": datetime.datetime.utcnow().isoformat()}
    goals_db[goal["id"]] = goal
    return goal

@app.get("/v1/autonomy/goals")
def list_goals(user=Depends(get_user)):
    return [g for g in goals_db.values() if g["workspaceId"] == user["workspaceId"]]

@app.get("/v1/autonomy/goals/{goal_id}")
def get_goal(goal_id: str, user=Depends(get_user)):
    goal = goals_db.get(goal_id)
    if not goal or goal["workspaceId"] != user["workspaceId"]: raise HTTPException(404, "Not found")
    return goal

@app.post("/v1/autonomy/goals/{goal_id}/approve")
def approve_goal(goal_id: str, user=Depends(get_user)):
    goal = goals_db.get(goal_id)
    if not goal: raise HTTPException(404, "Not found")
    goal["status"] = "executing"
    goal["events"].append({"type": "approved", "at": datetime.datetime.utcnow().isoformat(), "by": user["id"]})
    return goal

@app.post("/v1/autonomy/goals/{goal_id}/deny")
def deny_goal(goal_id: str, user=Depends(get_user)):
    goal = goals_db.get(goal_id)
    if not goal: raise HTTPException(404, "Not found")
    goal["status"] = "blocked"
    goal["events"].append({"type": "denied", "at": datetime.datetime.utcnow().isoformat(), "by": user["id"]})
    return goal

@app.post("/v1/autonomy/kill")
def kill_all(user=Depends(get_user)):
    count = 0
    for goal in goals_db.values():
        if goal["workspaceId"] == user["workspaceId"] and goal["status"] == "executing":
            goal["status"] = "paused"
            goal["events"].append({"type": "killed", "at": datetime.datetime.utcnow().isoformat(), "by": user["id"]})
            count += 1
    return {"ok": True, "killed": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
