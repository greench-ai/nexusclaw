"""
NexusClaw OpenRoom Web Server
Your framework. Your rules. — Running on port 19789
"""
import os, asyncio, json, uuid
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="NexusClaw OpenRoom", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent
API_URL = os.environ.get("NEXUS_API_URL", "http://localhost:8080")
PORT = int(os.environ.get("PORT", 19789))

# In-memory session store
sessions = {}

@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health():
    return {"ok": True, "service": "nexusclaw-openroom", "version": "1.0.0", "port": PORT}

@app.get("/api/status")
async def status():
    """Overall system status."""
    import aiohttp
    status = {"openroom": "online", "api": "unknown", "ollama": "unknown"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_URL}/health", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                status["api"] = "online" if resp.ok else f"error {resp.status}"
        except:
            status["api"] = "offline"
        
        try:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                if resp.ok:
                    data = await resp.json()
                    status["ollama"] = f"online ({len(data.get('models', []))} models)"
                else:
                    status["ollama"] = f"error {resp.status}"
        except:
            status["ollama"] = "offline"
    
    return status

@app.post("/api/sessions")
async def create_session(data: dict):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        "id": session_id,
        "title": data.get("title", "New Chat"),
        "messages": [],
        "created": str(uuid.uuid4()),
    }
    return sessions[session_id]

@app.get("/api/sessions")
async def list_sessions():
    """List all sessions."""
    return list(sessions.values())

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    return sessions.get(session_id, {"error": "not found"})

@app.websocket("/ws/{session_id}")
async def websocket_chat(ws: WebSocket, session_id: str):
    """WebSocket chat with streaming response."""
    await ws.accept()
    
    import aiohttp
    
    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id,
            "title": "Chat",
            "messages": [],
        }
    
    session = sessions[session_id]
    
    try:
        while True:
            data = await ws.receive_json()
            message = data.get("content", "")
            provider = data.get("provider", "ollama")
            model = data.get("model", "llama3.2")
            
            if not message:
                continue
            
            # Save user message
            session["messages"].append({"role": "user", "content": message})
            
            # Stream from API
            try:
                async with aiohttp.ClientSession() as http_session:
                    payload = {
                        "sessionId": session_id,
                        "message": message,
                        "provider": provider,
                        "model": model,
                    }
                    
                    async with http_session.post(
                        f"{API_URL}/v1/chat/answer/stream",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as resp:
                        if resp.status != 200:
                            await ws.send_json({"type": "error", "content": f"API error: {resp.status}"})
                            continue
                        
                        full_response = ""
                        async for line in resp.content:
                            text = line.decode().strip()
                            if text.startswith("data: "):
                                try:
                                    chunk = json.loads(text[6:])
                                    if chunk.get("type") == "chunk":
                                        content = chunk.get("content", "")
                                        full_response += content
                                        await ws.send_json({"type": "chunk", "content": content})
                                    elif chunk.get("type") == "done":
                                        await ws.send_json({"type": "done"})
                                except:
                                    pass
                        
                        # Save assistant message
                        if full_response:
                            session["messages"].append({"role": "assistant", "content": full_response})
                            
            except Exception as e:
                await ws.send_json({"type": "error", "content": str(e)})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "content": str(e)})
        except:
            pass

@app.on_event("startup")
async def startup():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║            NEXUSCLAW OPENROOM v1.0                  ║
║          Your framework. Your rules.                  ║
║                                                       ║
║  🌐 OpenRoom:  http://localhost:{PORT}               ║
║  🔗 API:        {API_URL:<38} ║
║                                                       ║
║  Your framework — configure it your way.             ║
╚══════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
