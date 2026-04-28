"""
NexusClaw Web UI Server
Serves the OpenRoom-inspired web UI + WebSocket for live updates.
"""
import os, asyncio, logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_HTML = ROOT / "apps" / "web" / "index.html"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
log = logging.getLogger("nexusclaw.web")

app = FastAPI(title="NexusClaw Web", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Active WebSocket connections
ws_connections: dict[str, list[WebSocket]] = {}


@app.get("/")
async def root():
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    return HTMLResponse("<h1>NexusClaw Web — index.html not found</h1>", status_code=404)


@app.get("/ui")
async def ui():
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    return HTMLResponse("<h1>NexusClaw Web — index.html not found</h1>", status_code=404)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(ws: WebSocket, client_id: str):
    """Live update broadcast channel."""
    await ws.accept()
    if client_id not in ws_connections:
        ws_connections[client_id] = []
    ws_connections[client_id].append(ws)
    log.info(f"WS client connected: {client_id} (total: {sum(len(v) for v in ws_connections.values())})")
    try:
        while True:
            data = await ws.receive_text()
            # Broadcast to all clients in same group
            for client in ws_connections.get(client_id, []):
                if client != ws:
                    try:
                        await client.send_text(data)
                    except Exception:
                        pass
    except WebSocketDisconnect:
        log.info(f"WS client disconnected: {client_id}")
    finally:
        if client_id in ws_connections:
            ws_connections[client_id] = [c for c in ws_connections[client_id] if c != ws]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexusclaw-web", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("NEXUS_WEB_PORT", "19789"))
    log.info(f"Starting NexusClaw Web UI on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
