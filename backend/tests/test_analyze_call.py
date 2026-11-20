import asyncio
import json
from pathlib import Path

from app.application.analyze_call import AnalyzeCall
from app.domain.call_analysis import CallToAnalyze, PromptPreview, build_prompt

RULES = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"
COMMON = json.loads((RULES / "_common.json").read_text(encoding="utf-8"))
PAY_BILL = json.loads((RULES / "pay_bill.json").read_text(encoding="utf-8"))
METADATA = {"agent": {"metadata": {"agent_name": "Dana"}}}
TRANSCRIPT = [{"index": 1, "speaker_role": "agent", "human_transcript": "Hi"}]


class FakeCalls:
    async def load(self, call_id):
        return CallToAnalyze(call_id, "abc", "pay_bill", METADATA, TRANSCRIPT, PAY_BILL)

    async def turns(self, call_id):
        return []


class FakeTemplate:
    async def load(self):
        return COMMON


class FakeModel:
    def __init__(self):
        self.asked = []

    async def ask(self, prompt, model):
        self.asked.append(prompt)
        return "deepseek-r1:8b", "{}"


def test_dry_run():
    model = FakeModel()

    result = asyncio.run(AnalyzeCall(calls=FakeCalls(), template=FakeTemplate(), model=model).execute(5, dry_run=True))

    assert result == PromptPreview(5, "abc", "pay_bill", build_prompt(COMMON, PAY_BILL, TRANSCRIPT, "Dana"))
    assert "Dana" in result.prompt and "[1] agent: Hi" in result.prompt
    assert model.asked == []
