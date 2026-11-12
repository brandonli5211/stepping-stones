"""Analysis settings (RULES_DIR, OLLAMA_*). Read only by the composition root (app.main)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from app.adapters.files.prompt_template import JsonPromptTemplate
from app.adapters.llm.ollama import OllamaModel, normalize_host

DEFAULT_RULES_DIR = Path(__file__).resolve().parents[3] / "docs" / "procedures" / "schema3"


def analysis_adapters_from_env(environ: Mapping[str, str]) -> tuple[JsonPromptTemplate, OllamaModel]:
    """The prompt template source and the model client. A non-numeric OLLAMA_TIMEOUT raises ValueError."""
    template = JsonPromptTemplate(Path(environ.get("RULES_DIR") or DEFAULT_RULES_DIR))
    model = OllamaModel(
        host=normalize_host(environ.get("OLLAMA_HOST", "http://localhost:11434")),
        default_model=environ.get("OLLAMA_MODEL", "deepseek-r1:8b"),
        timeout=float(environ.get("OLLAMA_TIMEOUT", "600")),
    )
    return template, model
