"""Hand-reviewed scoring calibration for every schema3 procedure template.

These scenarios use confident, verified observations so they exercise the real
ordered evaluator without depending on a model key or a database.  The failed
case for each template is its main customer-impacting action: the expected
losses are the intended rubric calibration, not evaluator implementation data.
"""

import asyncio
import json
from pathlib import Path

import pytest

from app.adapters.persistence.ordered_call_store import required_steps
from app.application.evaluate_ordered_call.input_data import EvaluateOrderedCallInputData
from app.application.evaluate_ordered_call.interactor import EvaluateOrderedCallInteractor
from app.domain.ordered_evaluation import CallForEvaluation, DecisionEvidence, StepDecision


RULES = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"

# One incorrect core action should have this impact.  These are deliberately
# explicit: changing a template's scoring requires a reviewer to change them.
CALIBRATED_FAILURES = [
    ("check_balance", "state_account_balance", "account_balance", 50),
    ("get_branch_hours", "state_branch_hours", None, 85),
    ("order_checks", "log_check_order", "home_address", 60),
    ("pay_bill", "log_bill_payment", "money_amount", 30),
    ("replace_card", "log_card_replacement", "replacement_card_type", 40),
    ("reset_password", "log_password_reset", "phone", 60),
    ("schedule_appointment", "log_appointment", "day", 20),
    ("transfer_money", "submit_and_confirm_transfer", "transfer_amount", 35),
]


class Store:
    def __init__(self, call):
        self.call = call
        self.saved = ()

    async def load_for_evaluation(self, call_id):
        return self.call if call_id == self.call.id else None

    async def save_evaluation(self, call, steps):
        self.saved = steps


class Model:
    def __init__(self, missing_step, facts):
        self.missing_step = missing_step
        self.facts = facts

    async def decide(self, call, step, minimum_evidence_turn):
        if step.key == self.missing_step:
            return StepDecision("not_yet_observed", .99, facts=self.facts)
        index = call.steps.index(step) + 1
        return StepDecision("completed_step", .99, DecisionEvidence(index, call.turn_texts[index]), facts=self.facts)


class Presenter:
    def present(self, output):
        return output


def procedure(call_type):
    return json.loads((RULES / f"{call_type}.json").read_text(encoding="utf-8"))


def calibration_call(call_type, changed_field=None):
    rules = procedure(call_type)
    steps = required_steps(rules)
    fields = [field["key"] for field in rules["fields"]]
    system_fields = {field["key"] for field in rules["fields"] if field["role"] == "told_to_caller"}
    facts = {f"{kind}:{field}": "right" for kind in ("request", "read_back") for field in fields}
    logged = {"task_type": call_type, **{field: "right" for field in fields}}
    system_record = {field: "right" for field in fields}
    if changed_field:
        if changed_field in system_fields:
            facts[f"read_back:{changed_field}"] = "wrong"
        else:
            logged[changed_field] = "wrong"
    call = CallForEvaluation(
        1, steps, {index: f"evidence {index}" for index in range(1, len(steps) + 1)},
        tuple(range(1, len(steps) + 1)), logged_actions=logged, call_ended=True,
        field_types={field: "text" for field in fields}, system_record=system_record,
    )
    return call, facts


@pytest.mark.parametrize("call_type, step_key, changed_field, expected_loss", CALIBRATED_FAILURES)
def test_each_template_scores_a_fully_correct_call_at_100(call_type, step_key, changed_field, expected_loss):
    call, facts = calibration_call(call_type)
    store = Store(call)
    output = asyncio.run(EvaluateOrderedCallInteractor(store, Model(None, facts), Presenter()).execute(EvaluateOrderedCallInputData(1)))

    assert (output.completed, output.wrong, output.missed, output.under_review) == (len(call.steps), 0, 0, 0)
    assert sum(step.points_lost for step in store.saved) == 0


@pytest.mark.parametrize("call_type, step_key, changed_field, expected_loss", CALIBRATED_FAILURES)
def test_each_template_applies_its_calibrated_core_failure(call_type, step_key, changed_field, expected_loss):
    call, facts = calibration_call(call_type, changed_field)
    store = Store(call)
    output = asyncio.run(EvaluateOrderedCallInteractor(store, Model(step_key if changed_field is None else None, facts), Presenter()).execute(EvaluateOrderedCallInputData(1)))

    failed = next(step for step in store.saved if step.key == step_key)
    assert (failed.status, failed.points_lost) == (("missed" if changed_field is None else "wrong"), expected_loss)
    assert sum(step.points_lost for step in store.saved) == expected_loss
    assert (output.wrong, output.missed, output.under_review) == (
        (0 if changed_field is None else 1), (1 if changed_field is None else 0), 0,
    )
