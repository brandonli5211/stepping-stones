"""Entry point for the API. Run with:  uvicorn app.main:app --reload

This file only wires things together. Real logic lives in routers/ (endpoints)
and, later, services/ (template checking, scoring).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import conversations

app = FastAPI(title="Stepping Stones API", version="0.1.0")

# Lets the React dev server (a different port = a different "origin") call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router)


@app.get("/api/health", tags=["health"])
def health():
    """Quick check that the API is up. Does not touch the database."""
    return {"status": "ok"}
