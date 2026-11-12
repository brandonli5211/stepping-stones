from pathlib import Path

import pytest
from fastapi import FastAPI

from app.adapters.files.prompt_template import JsonPromptTemplate
from app.adapters.llm.ollama import OllamaModel
from app.infrastructure.analysis_settings import DEFAULT_RULES_DIR, analysis_adapters_from_env
from app.main import configure_analysis


def test_default_rules_dir_is_schema3():
    assert DEFAULT_RULES_DIR == Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"
    assert (DEFAULT_RULES_DIR / "_common.json").is_file()


def test_defaults():
    template, model = analysis_adapters_from_env({})
    assert template.rules_dir == DEFAULT_RULES_DIR
    assert (model.host, model.default_model, model.timeout) == ("http://localhost:11434", "deepseek-r1:8b", 600.0)


def test_overrides():
    template, model = analysis_adapters_from_env(
        {"RULES_DIR": "/tmp/rules", "OLLAMA_HOST": "ollama:11434", "OLLAMA_MODEL": "llama3", "OLLAMA_TIMEOUT": "30"})
    assert template.rules_dir == Path("/tmp/rules")
    assert (model.host, model.default_model, model.timeout) == ("http://ollama:11434", "llama3", 30.0)


def test_empty_rules_dir_falls_back_to_default():
    template, _ = analysis_adapters_from_env({"RULES_DIR": ""})
    assert template.rules_dir == DEFAULT_RULES_DIR


def test_non_numeric_timeout_raises():
    with pytest.raises(ValueError):
        analysis_adapters_from_env({"OLLAMA_TIMEOUT": "soon"})


def test_configure_analysis_sets_app_state():
    app = FastAPI()
    configure_analysis(app, {"OLLAMA_MODEL": "llama3"})
    assert isinstance(app.state.prompt_template, JsonPromptTemplate)
    assert isinstance(app.state.language_model, OllamaModel)
    assert app.state.language_model.default_model == "llama3"


def test_main_app_state_has_analysis_adapters():
    import app.main

    assert isinstance(app.main.app.state.prompt_template, JsonPromptTemplate)
    assert isinstance(app.main.app.state.language_model, OllamaModel)
