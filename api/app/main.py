from typing import Literal

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings

app = FastAPI(title="telemetry-orchestrator")


class HealthResponse(BaseModel):
    status: Literal["ok"]


class DbHealthResponse(BaseModel):
    status: Literal["ok", "error"]
    db: Literal["reachable", "unreachable"]
    detail: str | None = None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/db", response_model=DbHealthResponse)
def health_db() -> DbHealthResponse:
    settings = get_settings()
    try:
        with (
            psycopg.connect(settings.database_url, connect_timeout=2) as conn,
            conn.cursor() as cur,
        ):
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as exc:
        return DbHealthResponse(status="error", db="unreachable", detail=str(exc))
    return DbHealthResponse(status="ok", db="reachable")
