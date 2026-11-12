import ast
import json
from pathlib import Path

import pytest

import app.domain.call_analysis as call_analysis
from app.domain.call_analysis import (
    CallNotFound,
    NoTranscript,
    agent_name_from_metadata,
    build_prompt,
    clean_answer,
    parse_answer,
    transcript_from_turns,
)

_RULES = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"
COMMON = json.loads((_RULES / "_common.json").read_text(encoding="utf-8"))
PROC = json.loads((_RULES / "transfer_money.json").read_text(encoding="utf-8"))
TRANSCRIPT = [
    {"index": 1, "speaker_role": "agent", "human_transcript": "Hello, how can I help?"},
    {"speaker_role": "caller", "human_transcript": "  ", "transcript": "send fifty dollars"},
]


# build_prompt

def test_build_prompt_fills_every_placeholder():
    prompt = build_prompt(COMMON, PROC, TRANSCRIPT, "Dana")
    assert "{{" not in prompt
    assert PROC["gate"]["question"] in prompt
    assert "Dana" in prompt
    for f in PROC["fields"]:
        assert f"- {f['key']} [" in prompt
    assert json.dumps(PROC["model_output_example"], indent=2) in prompt


def test_build_prompt_lists_only_eligible_steps():
    prompt = build_prompt(COMMON, PROC, TRANSCRIPT, "Dana")
    for s in PROC["steps"]:
        eligible = not s["sub_checks"] or any(c["type"] == "confirmation_evidence" for c in s["sub_checks"])
        assert (f'- "{s["key"]}" ({s["name"]})' in prompt) == eligible


def test_build_prompt_numbers_turns_and_falls_back_to_machine_text():
    prompt = build_prompt(COMMON, PROC, TRANSCRIPT, None)
    assert "[1] agent: Hello, how can I help?" in prompt
    assert "[2] caller: send fifty dollars" in prompt  # no index -> position; blank human text -> machine text
    assert "unknown" in prompt


# transcript_from_turns

def test_transcript_from_turns_numbers_from_one():
    assert transcript_from_turns([("agent", "Hi"), ("caller", "Hello")]) == [
        {"index": 1, "speaker_role": "agent", "human_transcript": "Hi"},
        {"index": 2, "speaker_role": "caller", "human_transcript": "Hello"},
    ]
    assert transcript_from_turns([]) == []


# agent_name_from_metadata

def test_agent_name_from_metadata():
    assert agent_name_from_metadata({"agent": {"metadata": {"agent_name": "Dana"}}}) == "Dana"
    assert agent_name_from_metadata({}) is None
    assert agent_name_from_metadata({"agent": None}) is None
    assert agent_name_from_metadata({"agent": {"metadata": None}}) is None


# clean_answer / parse_answer

def test_clean_answer_removes_every_think_block_across_lines():
    assert clean_answer("<think>a\nb</think> {\"x\": 1} <think>c</think>\n") == '{"x": 1}'
    assert clean_answer("  plain  ") == "plain"


def test_parse_answer_valid_and_invalid():
    assert parse_answer('{"x": 1}') == {"x": 1}
    assert parse_answer("not json") is None
    assert parse_answer("") is None


# errors

def test_error_messages():
    assert str(CallNotFound(7)) == "no call with id 7"
    assert str(NoTranscript(7)) == "call 7 has no transcript stored"


# layering

def test_domain_module_imports_nothing_outer():
    tree = ast.parse(Path(call_analysis.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint({"fastapi", "sqlalchemy", "alembic", "psycopg", "os", "urllib", "app"})

