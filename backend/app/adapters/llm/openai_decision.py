"""OpenAI Decisions adapter for observable, ordered call-step facts.

The Decisions API deliberately returns typed choices rather than generated JSON.
Each choice therefore names a stored agent turn.  The adapter turns a selected
turn into exact evidence; judging and persistence remain outside this adapter.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.request import Request, urlopen

from app.application.ports import ModelUnavailable
from app.domain.ordered_evaluation import CallForEvaluation, DecisionEvidence, RequiredStep, StepDecision

NOT_YET_OBSERVED = "not_yet_observed"
UNCLEAR = "unclear"
NOT_STATED = "not_stated"
DIFFERENT_VALUE = "different_value"


class OpenAIDecisionModel:
    """A narrow `StepDecisionModel` adapter backed by POST /v1/decisions."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com", model: str = "gpt-6-luna") -> None:
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/v1/decisions"
        self._model = model

    async def decide(self, call: CallForEvaluation, step: RequiredStep, minimum_evidence_turn: int) -> StepDecision:
        try:
            response = await asyncio.to_thread(self._post, self.request_body(call, step, minimum_evidence_turn))
        except Exception as error:  # Network and HTTP failures belong at the outer edge.
            raise ModelUnavailable(str(error)) from error
        return self.parse(response, call, step)

    def request_body(self, call: CallForEvaluation, step: RequiredStep, minimum_evidence_turn: int = 1) -> dict[str, Any]:
        allowed_turns = (
            sorted(call.turn_texts)
            if step.kind == "collection"
            else call.agent_turn_indices
        )
        choices = [
            {"value": f"turn:{index}", "description": call.turn_texts[index]}
            for index in allowed_turns
            if index >= minimum_evidence_turn and call.turn_texts.get(index)
        ]
        choices.extend((
            {"value": NOT_YET_OBSERVED, "description": "No listed agent turn satisfies this step."},
            {"value": UNCLEAR, "description": "The transcript is ambiguous, contradictory, or insufficient."},
        ))
        questions = [{
            "type": "choice", "name": "step_observation", "choices": choices,
            "instructions": (
                (
                    "Select the first transcript turn where this value is supplied by either speaker, "
                    "or where the agent asks for it. Do not judge recorded actions or a later read-back. "
                    "Choose not_yet_observed only when no turn supplies or requests the value; choose "
                    "unclear for ambiguity."
                    if step.kind == "collection"
                    else "Select the single agent turn that proves the procedure step was done. "
                    "Do not infer omitted facts. Choose not_yet_observed only when no turn satisfies it; "
                    "choose unclear for ambiguity or a contradiction."
                )
            ),
        }]
        logged = {key: (call.logged_actions or {}).get(key) for key in step.logged_action_keys}
        if step.kind == "confirmation":
            fields = sorted({field for check in step.checks for field in check.fields})
            for field in fields:
                choices = self._fact_choices(field, (call.logged_actions or {}).get(field))
                questions.extend(({
                    "type": "choice", "name": f"request:{field}", "choices": choices,
                    "instructions": "Select the value the caller requested. Do not judge whether it matches a record.",
                }, {
                    "type": "choice", "name": f"read_back:{field}", "choices": choices,
                    "instructions": "Select the value the agent said back. Do not judge whether it is correct.",
                }))
        return {
            "model": self._model,
            "input": [{"role": "user", "content": [{"type": "input_json", "data": {
                "procedure_step": {"key": step.key, "name": step.name, "done_when": step.done_when,
                                   "minimum_evidence_turn": minimum_evidence_turn, "logged_actions": logged},
                "transcript": [
                    {"turn": index, "speaker": "agent" if index in call.agent_turn_indices else "caller", "text": text}
                    for index, text in sorted(call.turn_texts.items())
                ],
            }}]}],
            "questions": questions,
        }

    @staticmethod
    def _fact_choices(field: str, logged: object) -> list[dict[str, str]]:
        """Finite literals let Decisions report a fact instead of a judgment."""
        key = field.lower()
        if "account" in key:
            values = ("checking", "savings")
        elif "card" in key:
            values = ("debit", "credit")
        elif key == "day":
            values = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
        else:
            values = (str(logged), DIFFERENT_VALUE) if logged not in (None, "") else (DIFFERENT_VALUE,)
        return ([{"value": value, "description": value} for value in values]
                + [{"value": NOT_STATED, "description": "The value is not stated."},
                   {"value": UNCLEAR, "description": "The value is ambiguous."}])

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self._url, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}, method="POST",
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed OpenAI endpoint or caller-supplied test endpoint
            return json.load(response)

    @staticmethod
    def parse(
        response: dict[str, Any], call: CallForEvaluation, step: RequiredStep | None = None
    ) -> StepDecision:
        answer = next((item for item in response.get("answers", ()) if item.get("name") == "step_observation"), None)
        if not answer or answer.get("type") == "refusal":
            return StepDecision(UNCLEAR, 0.0, raw_response=response)
        choice = answer.get("choice")
        try:
            confidence = float(answer.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        facts = {
            item["name"]: item.get("choice")
            for item in response.get("answers", ())
            if isinstance(item.get("name"), str)
            and (item["name"].startswith("request:") or item["name"].startswith("read_back:"))
            and item.get("choice") not in {None, NOT_STATED, UNCLEAR}
        }
        if choice == NOT_YET_OBSERVED:
            return StepDecision(choice, confidence, facts=facts, raw_response=response)
        if choice == UNCLEAR or not isinstance(choice, str) or not choice.startswith("turn:"):
            return StepDecision(
                UNCLEAR, confidence, facts=facts, raw_response=response,
            )
        try:
            index = int(choice.removeprefix("turn:"))
        except ValueError:
            return StepDecision(UNCLEAR, confidence, raw_response=response)
        text = call.turn_texts.get(index)
        allowed_turns = set(call.turn_texts) if step is not None and step.kind == "collection" else set(call.agent_turn_indices)
        if index not in allowed_turns or not text:
            return StepDecision(UNCLEAR, confidence, raw_response=response)
        return StepDecision(
            "completed_step", confidence, DecisionEvidence(index, text), facts=facts, raw_response=response,
        )
