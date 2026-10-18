import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="Stepping Stones API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Confirms the API is up and can reach Postgres."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
