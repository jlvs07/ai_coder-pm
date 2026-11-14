from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Kanban MVP API", version="0.1.0")
frontend_dir = Path(__file__).parent / "static"


@app.get("/health")
def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "kanban-api"})


@app.get("/api/hello")
def hello_api() -> JSONResponse:
    return JSONResponse({"message": "hello from the Kanban backend"})


if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:

    @app.get("/", response_class=HTMLResponse)
    def home_page() -> str:
        return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Kanban MVP</title>
        <style>
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #032147, #209dd7);
            color: white;
          }
          .card {
            padding: 2rem 3rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
            text-align: center;
          }
          h1 { margin-bottom: 0.5rem; }
          p { margin: 0.5rem 0; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Hello from Kanban MVP</h1>
          <p>The backend is running correctly.</p>
          <p>Use /health or /api/hello to verify the API.</p>
        </div>
      </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
