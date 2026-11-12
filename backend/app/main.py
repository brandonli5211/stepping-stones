import os
from collections.abc import Mapping

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.http.analyze import router as analyze_router
from app.adapters.http.calls import router as list_calls_router
from app.adapters.http.health import router as health_router
from app.infrastructure.analysis_settings import analysis_adapters_from_env
from app.infrastructure.clock import clock_from_env

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


def configure_clock(app: FastAPI, environ: Mapping[str, str]) -> None:
    """The only place DEMO_TODAY is read. A malformed value raises, so the API does not start."""
    app.state.clock = clock_from_env(environ)


def configure_analysis(app: FastAPI, environ: Mapping[str, str]) -> None:
    """The only place RULES_DIR and OLLAMA_* are read. A non-numeric OLLAMA_TIMEOUT raises, so the API does not start."""
    app.state.prompt_template, app.state.language_model = analysis_adapters_from_env(environ)


app = FastAPI(title="Stepping Stones API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_clock(app, os.environ)
configure_analysis(app, os.environ)
app.include_router(health_router)
app.include_router(list_calls_router)
app.include_router(analyze_router)
