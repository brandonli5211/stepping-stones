import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.http.call_detail import router as call_detail_router
from app.adapters.http.health import router as health_router
from app.calls_api import router as calls_router

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="Stepping Stones API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(calls_router)
app.include_router(call_detail_router)
