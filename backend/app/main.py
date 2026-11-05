import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.calls_api import router as calls_router
from app.db import get_session

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="Stepping Stones API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(calls_router)


@app.get("/api/health")
async def health(session: AsyncSession = Depends(get_session)):
    """Confirms the API is up and can reach Postgres."""
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
