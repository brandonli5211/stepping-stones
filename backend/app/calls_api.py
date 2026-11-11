"""POST /calls/{call_id}: look the call up in the database, build a prompt from its stored transcript and metadata,
and send it to a local Ollama model. The caller sends only our call id (and optionally a model or dry_run).

The procedure rules come from the call's procedure row (procedures.rules). The shared prompt template comes from
_common.json in docs/procedures/schema3 (set RULES_DIR to use another folder).
Env: OLLAMA_HOST (default http://localhost:11434), OLLAMA_MODEL (default deepseek-r1:8b), OLLAMA_TIMEOUT (seconds).
"""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.engine import get_session
from app.models import Call, CallTurn, Procedure

router = APIRouter()


class AnalyzeRequest(BaseModel):
    model: str | None = None  # Ollama model name; default OLLAMA_MODEL
    dry_run: bool = False  # True: return the prompt without calling the model



def load_common() -> dict:
    """The shared prompt template and field types (_common.json)."""
    folder = Path(os.getenv("RULES_DIR") or Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3")
    try:
        return json.loads((folder / "_common.json").read_text())
    except FileNotFoundError as exc:
        raise HTTPException(503, f"missing rules file: {exc.filename} (set RULES_DIR)")


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


def ask_ollama(prompt: str, model: str | None = None) -> tuple[str, str]:
    """Send the prompt to Ollama. Returns (model name, answer text)."""
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    if "://" not in host:
        host = "http://" + host
    name = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    payload = {"model": name, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0, "seed": 42}}
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=float(os.getenv("OLLAMA_TIMEOUT", "600"))) as resp:
        return name, json.load(resp)["response"]


@router.post("/calls/{call_id}")
async def analyze_call(call_id: int, body: AnalyzeRequest | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    """call_id is our own call id: the `id` that GET /calls returns."""
    body = body or AnalyzeRequest()
    call = (await session.execute(
        select(Call.id, Call.external_id, Call.call_type, Call.raw_metadata, Call.raw_transcript, Procedure.rules)
        .join(Procedure, Procedure.id == Call.procedure_id).where(Call.id == call_id)
    )).first()
    if call is None:
        raise HTTPException(404, f"no call with id {call_id}")

    transcript = call.raw_transcript
    if not transcript:  # calls loaded before raw_transcript existed: rebuild from the turns table
        turns = (await session.execute(select(CallTurn.speaker, CallTurn.text).where(CallTurn.call_id == call.id).order_by(CallTurn.idx))).all()
        transcript = [{"index": i, "speaker_role": t.speaker, "human_transcript": t.text} for i, t in enumerate(turns, 1)]
    if not transcript:
        raise HTTPException(422, f"call {call_id} has no transcript stored")

    agent_name = ((call.raw_metadata.get("agent") or {}).get("metadata") or {}).get("agent_name")
    prompt = build_prompt(load_common(), call.rules, transcript, agent_name)
    if body.dry_run:
        return {"id": call.id, "external_id": call.external_id, "call_type": call.call_type, "prompt": prompt}
    try:
        model, answer = await run_in_threadpool(ask_ollama, prompt, body.model)  # blocks for a while: keep it off the event loop
    except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
        raise HTTPException(503, f"could not get an answer from Ollama: {exc}")

    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip()  # DeepSeek-R1 reasoning
    try:
        parsed = json.loads(answer)
    except ValueError:
        parsed = None
    return {"id": call.id, "external_id": call.external_id, "call_type": call.call_type, "model": model, "result": parsed, "raw": answer}

