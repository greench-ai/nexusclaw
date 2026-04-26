"""
NexusClaw API Server
FastAPI-based backend with JWT auth, chat sessions, file upload, RAG indexing.
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid, jwt, datetime

app = FastAPI(title="NexusClaw API", version="0.1.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# In-memory store (replace with PostgreSQL in production)
users_db = {}
sessions_db = {}
files_db = {}
goals_db = {}

SECRET = "nexusclaw-dev-secret-change-in-production"

# === Auth Models ===
class RegisterRequest(BaseModel):
    email: str
    password: str
    displayName: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    sessionId: Optional[str] = None
    message: str
    citations: bool = True

class GoalRequest(BaseModel):
    title: str
    objective: str
    constraints: dict = {}

# === Auth Routes ===
@app.post("/health")
def health():
    return {"ok": True, "service": "nexusclaw-api", "version": "0.1.0"}

@app.post("/v1/auth/register")
def register(req: RegisterRequest):
    if req.email in users_db:
        raise HTTPException(400, "User already exists")
    user = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "passwordHash": req.password,  # TODO: hash
        "displayName": req.displayName,
        "workspaceId": str(uuid.uuid4()),
        "createdAt": datetime.datetime.utcnow().isoformat(),
    }
    users_db[req.email] = user
    token = jwt.encode({"sub": user["id"], "email": req.email}, SECRET, algorithm="HS256")
    return {"token": token, "user": user, "workspace": {"id": user["workspaceId"]}}

@app.post("/v1/auth/login")
def login(req: LoginRequest):
    user = users_db.get(req.email)
    if not user or user["passwordHash"] != req.password:
        raise HTTPException(401, "Invalid credentials")
    token = jwt.encode({"sub": user["id"], "email": req.email}, SECRET, algorithm="HS256")
    return {"token": token, "user": user, "workspace": {"id": user["workspaceId"]}}

def get_user(authorization: str = ""):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    try:
        token = authorization[7:]
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return users_db[payload["email"]]
    except:
        raise HTTPException(401, "Invalid token")

# === Chat Routes ===
@app.post("/v1/chat/sessions")
def create_session(user=Depends(get_user), title: str = "New Session"):
    session = {"id": str(uuid.uuid4()), "userId": user["id"], "title": title, "messages": [], "createdAt": datetime.datetime.utcnow().isoformat()}
    sessions_db[session["id"]] = session
    return session

@app.get("/v1/chat/sessions")
def list_sessions(user=Depends(get_user)):
    return [s for s in sessions_db.values() if s["userId"] == user["id"]]

@app.post("/v1/chat/answer/stream")
def stream_answer(req: ChatRequest, user=Depends(get_user)):
    """Streaming chat endpoint — returns SSE events."""
    # This would connect to the model gateway in production
    return {"message": "Use WebSocket for streaming in production", "sessionId": req.sessionId}

# === File Upload ===
@app.post("/v1/files/upload")
async def upload_file(file: UploadFile = File(...), user=Depends(get_user)):
    content = await file.read()
    file_id = str(uuid.uuid4())
    files_db[file_id] = {
        "fileId": file_id,
        "userId": user["id"],
        "filename": file.filename,
        "size": len(content),
        "status": "queued",  # queued -> indexing -> ready
        "createdAt": datetime.datetime.utcnow().isoformat(),
    }
    # TODO: enqueue to worker
    return {"ok": True, "fileId": file_id, "status": "queued"}

# === Autonomous Goals ===
@app.post("/v1/autonomy/goals")
def create_goal(req: GoalRequest, user=Depends(get_user)):
    goal = {
        "id": str(uuid.uuid4()),
        "workspaceId": user["workspaceId"],
        "creatorUserId": user["id"],
        "title": req.title,
        "objective": req.objective,
        "constraints": req.constraints,
        "status": "queued",
        "tasks": [],
        "events": [],
        "createdAt": datetime.datetime.utcnow().isoformat(),
    }
    goals_db[goal["id"]] = goal
    return goal

@app.get("/v1/autonomy/goals")
def list_goals(user=Depends(get_user)):
    return [g for g in goals_db.values() if g["workspaceId"] == user["workspaceId"]]

@app.post("/v1/autonomy/goals/{goal_id}/approve")
def approve_goal(goal_id: str, user=Depends(get_user)):
    goal = goals_db.get(goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    goal["status"] = "executing"
    goal["events"].append({"type": "approved", "at": datetime.datetime.utcnow().isoformat(), "by": user["id"]})
    return goal

@app.post("/v1/autonomy/goals/{goal_id}/kill")
def kill_goal(goal_id: str, user=Depends(get_user)):
    goal = goals_db.get(goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    goal["status"] = "paused"
    goal["events"].append({"type": "killed", "at": datetime.datetime.utcnow().isoformat(), "by": user["id"]})
    return {"ok": True, "goalId": goal_id, "status": "paused"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
