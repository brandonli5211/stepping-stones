import asyncio
import json
import os
from typing import Any
from urllib.request import Request, urlopen

from app.domain.procedure import AgentTurnWindow, CallCursor, ProcedureStep, StepDecision


class OpenAIDecisionsAdapter:
    """Outer adapter for OpenAI's binary step-observation Decision."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ["OPENAI_API_KEY"]
        self._url = f"{(base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com')).rstrip('/')}/v1/decisions"

    async def __call__(
        self, procedure_id: str, task_id: str, step: ProcedureStep, window: AgentTurnWindow, cursor: CallCursor
    ) -> StepDecision:
        body = self._request_body(procedure_id, task_id, step, window, cursor)
        response = await asyncio.to_thread(self._post, body)
        return self._parse(response)

    @staticmethod
    def _request_body(
        procedure_id: str, task_id: str, step: ProcedureStep, window: AgentTurnWindow, cursor: CallCursor
    ) -> dict[str, Any]:
        return {
            "model": "gpt-6-luna",
            "input": [{"role": "user", "content": [{"type": "input_json", "data": {
                "procedure_id": procedure_id, "task_id": task_id,
                "current_step": {"id": step.id, "objective": step.objective,
                    "evidence_requirements": step.evidence_requirements,
                    "acceptable_variants": step.acceptable_variants, "exclusions": step.exclusions},
                "current_agent_turn": window.agent_turn, "surrounding_context": window.surrounding_context,
                "call_cursor": {"expected_step_index": cursor.expected_step_index,
                    "agent_turn_index": cursor.agent_turn_index, "call_ended": cursor.call_ended},
            }}]}],
            "questions": [{"type": "choice", "name": "expected_step_observation",
                "instructions": "Use only observable evidence. Select completed_step only when this turn satisfies the current step without exclusions; otherwise select not_yet_observed.",
                "choices": [{"value": "completed_step"}, {"value": "not_yet_observed"}]}],
        }

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(self._url, data=json.dumps(body).encode(), headers={
            "Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed OpenAI endpoint/configured base URL
            return json.load(response)

    @staticmethod
    def _parse(response: dict[str, Any]) -> StepDecision:
        answer = next((item for item in response.get("answers", []) if item.get("name") == "expected_step_observation"), None)
        if not answer or answer.get("choice") not in {"completed_step", "not_yet_observed"}:
            raise ValueError("Decisions response lacks a valid expected_step_observation answer")
        return StepDecision(choice=answer["choice"], confidence=float(answer.get("confidence", 0)), evidence_metadata={"decision": answer})
