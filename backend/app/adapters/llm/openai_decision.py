"""Select transcript observations with the typed OpenAI Decisions API."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.request import Request, urlopen

from app.adapters.llm.spoken_amounts import amount_candidates
from app.application.ports import ModelUnavailable
from app.domain.ordered_evaluation import (
    CONFIDENT_FACT_THRESHOLD, DIFFERENT_VALUE, NOT_STATED,
    CallForEvaluation, DecisionEvidence, RequiredStep, StepDecision,
)

NOT_YET_OBSERVED = "not_yet_observed"
UNCLEAR = "unclear"
ENUM_VALUES = {
    "account": ("checking", "savings"),
    "card_type": ("debit", "credit"),
    "day": ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"),
}


def _field_description(call: CallForEvaluation, field: str) -> str:
    return f"{field.replace('_', ' ')}. {call.field_hints.get(field, '')}".strip()


def _observation_prompt(call: CallForEvaluation, step: RequiredStep) -> str | None:
    if step.kind == "collection":
        fields = " ".join(_field_description(call, key) for key in step.logged_action_keys)
        return (f"Locate the earliest mention of this field: {fields} Scan the listed turns from earliest to latest. "
                "Choose the first where either speaker states its value or the agent asks for this specific field. "
                "A volunteered caller value counts immediately, even if several values occur in that same turn "
                "or a later agent read-back is wrong.")
    if step.kind == "simple":
        return "Select the first listed agent turn where the agent says the words or performs the action described."
    kinds = {check.kind for check in step.checks}
    if "confirmation_evidence" in kinds:
        return ("Select the first agent turn confirming the action was taken. Cite the confirmation even if the "
                "agent states a different value from the caller's request.")
    if "read_back_matches_request" in kinds:
        return ("Select the first agent turn that reads back any of the requested details to the caller. Cite a "
                "partial or incorrect read-back too, even if a later turn repeats it or adds more details.")
    if "stated_matches_system_record" in kinds:
        return "Select the first agent turn that states the requested information to the caller, whatever value it gives."
    return None  # Logging a form is judged from the record and the caller's request.


def _questions(call: CallForEvaluation, step: RequiredStep, cursor: int) -> list[dict]:
    questions = []
    prompt = _observation_prompt(call, step)
    if prompt:
        indices = sorted(call.turn_texts) if step.kind == "collection" else call.agent_turn_indices
        choices = [{"value": f"turn:{idx}", "description":
                    f"{'Agent' if idx in call.agent_turn_indices else 'Caller'}: {call.turn_texts[idx]}"}
                   for idx in indices if idx >= cursor and call.turn_texts.get(idx)]
        choices.extend([
            {"value": NOT_YET_OBSERVED, "description": "No listed turn contains that observation."},
            {"value": UNCLEAR, "description": "The evidence is ambiguous."},
        ])
        questions.append({"type": "choice", "name": "step_observation", "choices": choices, "instructions": prompt})

    fields = dict.fromkeys(field for check in step.checks for field in check.fields)
    for field in fields:
        kinds = {check.kind for check in step.checks if field in check.fields}
        field_type = (call.field_types or {}).get(field)
        system_field = "stated_matches_system_record" in kinds
        if system_field:
            # The private bank reference must never be a model choice.
            candidates = amount_candidates(call.turn_texts[idx] for idx in call.agent_turn_indices if idx >= cursor)
        else:
            logged = (call.logged_actions or {}).get(field)
            candidates = ENUM_VALUES.get(field_type, ())
            if logged not in (None, "") and str(logged).strip().casefold() not in candidates:
                candidates = (*candidates, str(logged))
        choices = [{"value": value, "description": value} for value in candidates]
        if not system_field:
            choices.append({"value": DIFFERENT_VALUE, "description": "A value is stated but is outside the listed values."})
        choices.extend([
            {"value": NOT_STATED, "description": "This speaker never stated the field."},
            {"value": UNCLEAR, "description": "Unable to establish the stated value from the available choices."},
        ])
        field_description = _field_description(call, field)
        if kinds & {"logged_matches_request", "read_back_matches_request"}:
            questions.append({"type": "choice", "name": f"request:{field}", "choices": choices,
                              "instructions": f"Extract the caller's requested {field_description} Read only the "
                              "caller_statements. Use the last value the caller explicitly names for this field "
                              "anywhere in those statements. A bare 'yes' or 'okay' supplies no new value and "
                              "does not replace what the caller explicitly requested."})
        if kinds & {"read_back_matches_request", "stated_matches_system_record"}:
            questions.append({"type": "choice", "name": f"read_back:{field}", "choices": choices,
                              "instructions": f"Extract the agent's stated {field_description} Read only the "
                              f"agent_statements at or after turn {cursor}. "
                              "Use the agent's final statement of this field, even if incorrect. "
                              "A request for information does not state a value."})
    return questions


def _selected(response: dict, questions: list[dict]) -> dict[str, tuple[str, float]]:
    """Keep a unique, well-formed answer to each question actually offered."""
    options = {q["name"]: {c["value"] for c in q["choices"]} for q in questions}
    items = response.get("answers") if isinstance(response, dict) else None
    selected = {}
    seen = set()
    for item in items if isinstance(items, list) else ():
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or name not in options:
            continue
        if name in seen:
            selected.pop(name, None)
            continue
        seen.add(name)
        choice, confidence = item.get("choice"), item.get("confidence")
        if (item.get("type", "choice") == "choice" and isinstance(choice, str) and choice in options[name]
                and type(confidence) in (int, float) and 0 <= confidence <= 1):
            selected[name] = (choice, confidence)
    return selected


def _body(model: str, data: dict, questions: list[dict]) -> dict:
    return {"model": model, "input": [{"role": "user", "content": [{"type": "input_json", "data": data}]}],
            "questions": questions}


def _confirmation_requests(body: dict):
    """Give each group only the speaker who can supply its facts."""
    context = body["input"][0]["content"][0]["data"]
    for group, speech in (("step_observation", "agent_statements"), ("request", "caller_statements"),
                          ("read_back", "agent_statements")):
        questions = [q for q in body["questions"] if q["name"].partition(":")[0] == group]
        if questions:
            data = {"procedure_step": context["procedure_step"], speech: context[speech]}
            yield group, _body(body["model"], data, questions)


class OpenAIDecisionModel:
    """A narrow StepDecisionModel adapter backed by POST /v1/decisions."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com", model: str = "gpt-6-luna") -> None:
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/v1/decisions"
        self._model = model

    async def decide(self, call: CallForEvaluation, step: RequiredStep, minimum_evidence_turn: int) -> StepDecision:
        body = self.request_body(call, step, minimum_evidence_turn)
        if not body["questions"]:
            return StepDecision(UNCLEAR, 0.0, facts={})
        try:
            if step.kind == "confirmation":
                answers = []
                responses = {}
                for group, request in _confirmation_requests(body):
                    raw = await asyncio.to_thread(self._post, request)
                    responses[group] = raw
                    names = {q["name"] for q in request["questions"]}
                    items = raw.get("answers") if isinstance(raw, dict) else None
                    if isinstance(items, list):
                        answers.extend(a for a in items if isinstance(a, dict) and isinstance(a.get("name"), str)
                                       and a["name"] in names)
                response = {"model": self._model, "answers": answers, "responses": responses}
            else:
                response = await asyncio.to_thread(self._post, body)
        except Exception as error:
            raise ModelUnavailable(str(error)) from error
        return self.parse(response, call, step, minimum_evidence_turn)

    def request_body(self, call: CallForEvaluation, step: RequiredStep, minimum_evidence_turn: int = 1) -> dict[str, Any]:
        context = {"key": step.key, "name": step.name}
        if step.kind == "simple":
            context["done_when"] = step.done_when
        turns = [{"turn": idx, "speaker": "agent" if idx in call.agent_turn_indices else "caller", "text": text}
                 for idx, text in sorted(call.turn_texts.items())]
        if step.kind == "confirmation":
            speech = {"caller_statements": [t for t in turns if t["speaker"] == "caller"],
                      "agent_statements": [t for t in turns if t["speaker"] == "agent" and t["turn"] >= minimum_evidence_turn]}
        else:
            speech = {"transcript": turns}
        return _body(self._model, {"procedure_step": context, **speech}, _questions(call, step, minimum_evidence_turn))

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self._url, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}, method="POST",
        )
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    @staticmethod
    def parse(response: dict, call: CallForEvaluation, step: RequiredStep, minimum_evidence_turn: int = 1) -> StepDecision:
        answers = _selected(response, _questions(call, step, minimum_evidence_turn))
        choice, confidence = answers.pop("step_observation", (UNCLEAR, 0.0))
        facts = {name: value for name, (value, prob) in answers.items()
                 if prob >= CONFIDENT_FACT_THRESHOLD and value != UNCLEAR}
        evidence = None
        if choice.startswith("turn:"):
            index = int(choice.removeprefix("turn:"))
            evidence = DecisionEvidence(index, call.turn_texts[index])
            choice = "completed_step"
        return StepDecision(choice, confidence, evidence, facts=facts, raw_response=response)
