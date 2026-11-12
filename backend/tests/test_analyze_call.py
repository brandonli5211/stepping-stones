import ast
import asyncio
import json
from pathlib import Path

import pytest

import app.application.analyze_call as use_case_module
import app.application.ports as ports_module
from app.application.analyze_call import AnalyzeCall
from app.application.ports import ModelUnavailable, RulesUnavailable
from app.domain.call_analysis import (
    CallNotFound,
    CallToAnalyze,
    ModelAnalysis,
    NoTranscript,
    PromptPreview,
    build_prompt,
)

_RULES = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"
COMMON = json.loads((_RULES / "_common.json").read_text(encoding="utf-8"))
PROC = json.loads((_RULES / "pay_bill.json").read_text(encoding="utf-8"))
META = {"agent": {"metadata": {"agent_name": "Dana"}}}
RAW = [{"index": 1, "speaker_role": "agent", "human_transcript": "Hi"}]


def call(raw=RAW):
    return CallToAnalyze(id=5, external_id="abc", call_type="pay_bill", metadata=META, raw_transcript=raw, rules=PROC)


class FakeCalls:
    def __init__(self, found, turns=()):
        self.found, self._turns, self.log = found, list(turns), []

    async def load(self, call_id):
        self.log.append(("load", call_id))
        return self.found

    async def turns(self, call_id):
        self.log.append(("turns", call_id))
        return self._turns


class FakeTemplate:
    def __init__(self, error=None):
        self.error, self.loads = error, 0

    async def load(self):
        self.loads += 1
        if self.error:
            raise self.error
        return COMMON


class FakeModel:
    def __init__(self, answer="{}", error=None):
        self.answer, self.error, self.asked = answer, error, []

    async def ask(self, prompt, model):
        self.asked.append((prompt, model))
        if self.error:
            raise self.error
        return model or "deepseek-r1:8b", self.answer


def run(calls, template=None, model=None, **kw):
    use_case = AnalyzeCall(calls=calls, template=template or FakeTemplate(), model=model or FakeModel())
    return asyncio.run(use_case.execute(5, **kw))


def test_dry_run_returns_prompt_without_asking_model():
    model = FakeModel()
    result = run(FakeCalls(call()), model=model, dry_run=True)
    assert result == PromptPreview(5, "abc", "pay_bill", build_prompt(COMMON, PROC, RAW, "Dana"))
    assert model.asked == []


def test_turns_are_used_only_when_raw_transcript_is_empty():
    calls = FakeCalls(call(raw=[]), turns=[("agent", "Hello")])
    result = run(calls, dry_run=True)
    assert ("turns", 5) in calls.log
    assert "[1] agent: Hello" in result.prompt
    with_raw = FakeCalls(call())
    run(with_raw, dry_run=True)
    assert with_raw.log == [("load", 5)]


def test_missing_call_is_not_found_before_anything_else():
    template = FakeTemplate()
    with pytest.raises(CallNotFound, match="no call with id 5"):
        run(FakeCalls(None), template=template, dry_run=True)
    assert template.loads == 0


def test_no_transcript_comes_before_the_template():
    template = FakeTemplate(error=RulesUnavailable("/x/_common.json"))
    with pytest.raises(NoTranscript, match="call 5 has no transcript stored"):
        run(FakeCalls(call(raw=[]), turns=[]), template=template, dry_run=True)
    assert template.loads == 0


def test_rules_unavailable_propagates_on_dry_run():
    with pytest.raises(RulesUnavailable, match=r"missing rules file: /x/_common.json \(set RULES_DIR\)"):
        run(FakeCalls(call()), template=FakeTemplate(error=RulesUnavailable("/x/_common.json")), dry_run=True)


def test_model_answer_is_cleaned_and_parsed():
    model = FakeModel(answer='<think>x\ny</think>{"a": 1}')
    result = run(FakeCalls(call()), model=model)
    assert result == ModelAnalysis(5, "abc", "pay_bill", "deepseek-r1:8b", {"a": 1}, '{"a": 1}')
    assert model.asked[0][0] == build_prompt(COMMON, PROC, RAW, "Dana")


def test_non_json_answer_has_no_result():
    result = run(FakeCalls(call()), model=FakeModel(answer="sorry, no idea"))
    assert (result.result, result.raw) == (None, "sorry, no idea")


def test_model_name_is_passed_through():
    model = FakeModel()
    result = run(FakeCalls(call()), model=model, model_name="llama3")
    assert model.asked[0][1] == "llama3"
    assert result.model == "llama3"


def test_model_unavailable_propagates():
    with pytest.raises(ModelUnavailable, match="could not get an answer from Ollama: refused"):
        run(FakeCalls(call()), model=FakeModel(error=ModelUnavailable("refused")))


def test_application_modules_import_nothing_outer():
    for module in (use_case_module, ports_module):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(n.split(".", 1)[0] in {"fastapi", "sqlalchemy", "alembic", "psycopg", "os", "urllib"} for n in imported)
        assert not any(n.startswith(("app.adapters", "app.infrastructure")) for n in imported)
