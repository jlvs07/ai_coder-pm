from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.ai import router as ai_router
from app.api.boards import router as boards_router
from app.api.system import router as system_router
from app.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Kanban MVP API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(system_router)
    application.include_router(boards_router)
    application.include_router(ai_router)

    frontend_dir = Path(__file__).parent / "static"
    if frontend_dir.is_dir():
        application.mount(
            "/",
            StaticFiles(directory=frontend_dir, html=True),
            name="frontend",
        )
    else:

        @application.get("/", response_class=HTMLResponse)
        def home_page() -> str:
            return """
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>Kanban MVP</title>
              </head>
              <body>
                <h1>Hello from Kanban MVP</h1>
                <p>The backend is running correctly.</p>
                <p>Use /health or /api/hello to verify the API.</p>
              </body>
            </html>
            """

    return application


app = create_app()
