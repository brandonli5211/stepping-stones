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
        return self.parse(response, call)

    def request_body(self, call: CallForEvaluation, step: RequiredStep, minimum_evidence_turn: int = 1) -> dict[str, Any]:
        choices = [
            {"value": f"turn:{index}", "description": call.turn_texts[index]}
            for index in call.agent_turn_indices
            if index >= minimum_evidence_turn and call.turn_texts.get(index)
        ]
        choices.extend((
            {"value": NOT_YET_OBSERVED, "description": "No listed agent turn satisfies this step."},
            {"value": UNCLEAR, "description": "The transcript is ambiguous, contradictory, or insufficient."},
        ))
        questions = [{
            "type": "choice", "name": "step_observation", "choices": choices,
            "instructions": (
                "Select the single agent turn that proves the procedure step was done. "
                "Do not infer omitted facts. Choose not_yet_observed only when no turn satisfies it; "
                "choose unclear for ambiguity or a contradiction."
            ),
        }]
        logged = {key: (call.logged_actions or {}).get(key) for key in step.logged_action_keys}
        if step.checks_logged_actions:
            questions.append({
                "type": "choice", "name": "logged_actions_match", "choices": [
                    {"value": "match", "description": "Every recorded value agrees with what the caller requested."},
                    {"value": "mismatch", "description": "At least one recorded value conflicts with the caller's request or is absent."},
                    {"value": UNCLEAR, "description": "The transcript cannot establish the requested value."},
                ],
                "instructions": "Compare these recorded form values to the caller's own transcript, not to any outside answer key.",
            })
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

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self._url, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}, method="POST",
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed OpenAI endpoint or caller-supplied test endpoint
            return json.load(response)

    @staticmethod
    def parse(response: dict[str, Any], call: CallForEvaluation) -> StepDecision:
        answer = next((item for item in response.get("answers", ()) if item.get("name") == "step_observation"), None)
        if not answer or answer.get("type") == "refusal":
            return StepDecision(UNCLEAR, 0.0, raw_response=response)
        choice = answer.get("choice")
        try:
            confidence = float(answer.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        action_answer = next((item for item in response.get("answers", ()) if item.get("name") == "logged_actions_match"), None)
        actions_match: bool | None = True
        action_confidence: float | None = None
        if action_answer is not None:
            if action_answer.get("type") == "refusal" or action_answer.get("choice") == UNCLEAR:
                actions_match = None
            else:
                actions_match = action_answer.get("choice") == "match"
            try:
                action_confidence = float(action_answer.get("confidence", 0.0))
            except (TypeError, ValueError):
                actions_match = None
        if choice == NOT_YET_OBSERVED:
            return StepDecision(choice, confidence, logged_actions_match=actions_match,
                                action_confidence=action_confidence, raw_response=response)
        if choice == UNCLEAR or not isinstance(choice, str) or not choice.startswith("turn:"):
            return StepDecision(
                UNCLEAR, confidence, logged_actions_match=actions_match,
                action_confidence=action_confidence, raw_response=response,
            )
        try:
            index = int(choice.removeprefix("turn:"))
        except ValueError:
            return StepDecision(UNCLEAR, confidence, raw_response=response)
        text = call.turn_texts.get(index)
        if index not in call.agent_turn_indices or not text:
            return StepDecision(UNCLEAR, confidence, raw_response=response)
        return StepDecision(
            "completed_step", confidence, DecisionEvidence(index, text), logged_actions_match=actions_match,
            action_confidence=action_confidence, raw_response=response,
        )
