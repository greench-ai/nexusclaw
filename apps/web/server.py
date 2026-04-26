"""
NexusClaw OpenRoom Web Server
Serves the web UI + WebSocket proxy to API
"""
import os, asyncio, json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="NexusClaw OpenRoom")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent
API_URL = os.environ.get("NEXUS_API_URL", "http://localhost:8080")

@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health():
    return {"ok": True, "service": "nexusclaw-openroom", "version": "0.5.0"}

@app.websocket("/ws")
async def websocket_proxy(ws: WebSocket):
    """Proxy WebSocket → API backend."""
    await ws.accept()
    
    # Connect to API WebSocket
    import aiohttp
    async with aiohttp.ClientSession() as session:
        api_ws_url = API_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws/main"
        
        try:
            async with session.ws_connect(api_ws_url) as api_ws:
                async def forward_to_api():
                    async for msg in ws.iter_text():
                        await api_ws.send_str(msg)
                
                async def forward_to_client():
                    async for msg in api_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await ws.send_text(msg.data)
                
                await asyncio.gather(forward_to_api(), forward_to_client())
        except Exception as e:
            await ws.send_json({"type": "error", "content": f"Backend error: {e}"})

@app.on_event("startup")
async def startup():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║              NEXUSCLAW OPENROOM v0.5                   ║
║         Your framework. Your rules.                    ║
║                                                         ║
║  Web UI:  http://localhost:51234                       ║
║  API:     {API_URL:<42} ║
╚══════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=51234, log_level="info")
