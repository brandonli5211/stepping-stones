"""Pure rules for analyzing one call: the prompt, the transcript fallback, the agent name, and the answer.

Standard library only. No FastAPI, SQLAlchemy, Alembic, psycopg, HTTP clients, or environment access.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CallToAnalyze:
    id: int
    external_id: str
    call_type: str
    metadata: dict
    raw_transcript: list[dict]
    rules: dict


@dataclass(frozen=True)
class PromptPreview:
    id: int
    external_id: str
    call_type: str
    prompt: str


@dataclass(frozen=True)
class ModelAnalysis:
    id: int
    external_id: str
    call_type: str
    model: str
    result: Any
    raw: str


class CallNotFound(Exception):
    def __init__(self, call_id: int) -> None:
        super().__init__(f"no call with id {call_id}")
        self.call_id = call_id


class NoTranscript(Exception):
    def __init__(self, call_id: int) -> None:
        super().__init__(f"call {call_id} has no transcript stored")
        self.call_id = call_id


def build_prompt(common: dict, proc: dict, transcript: list[dict], agent_name: str | None) -> str:
    """Fill the prompt template with the procedure's steps and fields and the numbered transcript.
    The logged values and assigned task are never put in the prompt."""
    steps = "\n".join(
        f'- "{s["key"]}" ({s["name"]}): {s["done_when"]}  For example: "{s["example_phrase"]}"'
        for s in proc["steps"]
        if not s["sub_checks"] or any(c["type"] == "confirmation_evidence" for c in s["sub_checks"])
    )
    fields = "\n".join(
        f'- {f["key"]} [{", ".join(f["model_reports"])}]: {common["field_types"][f["type"]]["model_value"]}. {f["model_hint"]}'
        for f in proc["fields"]
    )
    lines = []
    for i, t in enumerate(transcript, 1):
        text = (t.get("human_transcript") or "").strip() or (t.get("transcript") or "").strip()
        lines.append(f"[{t.get('index', i)}] {t['speaker_role']}: {text}")
    return (
        common["prompt_template"]
        .replace("{{agent_name}}", agent_name or "unknown")
        .replace("{{gate_question}}", proc["gate"]["question"])
        .replace("{{steps}}", steps)
        .replace("{{fields}}", fields)
        .replace("{{transcript}}", "\n".join(lines))
        .replace("{{output_format}}", json.dumps(proc["model_output_example"], indent=2))
    )


def transcript_from_turns(turns: list[tuple[str, str]]) -> list[dict]:
    """Rebuild a transcript from stored (speaker, text) turns, numbered from 1 by position."""
    return [{"index": i, "speaker_role": speaker, "human_transcript": text} for i, (speaker, text) in enumerate(turns, 1)]


def agent_name_from_metadata(metadata: dict) -> str | None:
    return ((metadata.get("agent") or {}).get("metadata") or {}).get("agent_name")


def clean_answer(text: str) -> str:
    """Drop DeepSeek-R1 style <think>…</think> reasoning blocks and trim."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def parse_answer(cleaned: str) -> Any:
    """The answer as JSON, or None when it is not valid JSON."""
    try:
        return json.loads(cleaned)
    except ValueError:
        return None
