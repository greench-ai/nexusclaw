"""
NexusClaw API Server.
Direct provider APIs — no LiteLLM.
Serves web UI + API.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from nexusclaw.api import router as api_router
from nexusclaw.config import get_config_path, load_config

log = structlog.get_logger(__name__)


class AppState:
    config = load_config(get_config_path())


app_state = AppState()


def create_app() -> FastAPI:
    app = FastAPI(title="NexusClaw ⚡")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API Routes ──────────────────────────────────────────────────────────
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    # ── Serve web UI (React build) ──────────────────────────────────────────
    web_dist = Path("/app/web/dist")
    if web_dist.exists():

        @app.get("/assets/{path:path}")
        async def serve_assets(path: str):
            return FileResponse(web_dist / "assets" / path)

        @app.get("/setup")
        async def serve_setup():
            setup_path = web_dist.parent / "setup.html"
            if setup_path.exists():
                return FileResponse(setup_path)
            from starlette.responses import RedirectResponse
            return RedirectResponse(url="/")

        @app.get("/")
        async def serve_index():
            return FileResponse(web_dist / "index.html")

        @app.get("/chat")
        async def serve_chat():
            return FileResponse(web_dist / "index.html")

        # SPA fallback — single-level paths only (no slashes)
        # This prevents matching /api/* which must be handled by WebSocket/HTTP routes
        @app.get("/{path}")
        async def serve_spa_single(path: str):
            if "/" in path:
                return Response(status_code=404)
            file_path = web_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(web_dist / "index.html")

    return app


app = create_app()
