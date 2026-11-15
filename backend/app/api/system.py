from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "kanban-api"})


@router.get("/api/hello")
def hello_api() -> JSONResponse:
    return JSONResponse({"message": "hello from the Kanban backend"})
