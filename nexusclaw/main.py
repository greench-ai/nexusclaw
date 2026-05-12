"""
NexusClaw API Server.
Direct provider APIs — no LiteLLM.
Serves web UI + API.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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

        @app.get("/setup")
        async def serve_setup():
            setup_path = web_dist.parent / "setup.html"
            if setup_path.exists():
                return FileResponse(setup_path)
            return RedirectResponse(url="/")

        @app.get("/")
        async def serve_index():
            config = app_state.config
            # If no providers configured, show setup
            if not config.providers:
                setup_path = web_dist.parent / "setup.html"
                if setup_path.exists():
                    return FileResponse(setup_path)
            return FileResponse(web_dist / "index.html")

        @app.get("/chat")
        async def serve_chat():
            return FileResponse(web_dist / "index.html")

        @app.get("/assets/{path:path}")
        async def serve_assets(path: str):
            return FileResponse(web_dist / "assets" / path)

        @app.get("/{path:path}")
        async def serve_spa(path: str):
            file_path = web_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(web_dist / "index.html")

    return app


app = create_app()
