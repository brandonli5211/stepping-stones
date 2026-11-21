import asyncio
from types import SimpleNamespace as Row

import pytest

from app.adapters.http.call_detail import get_call_detail
from app.adapters.persistence.call_detail_reader import SqlAlchemyCallDetailReader
from app.adapters.persistence.ordered_call_store import SqlAlchemyOrderedCallStore, required_steps, severity
from app.application.get_call_detail import GetCallDetail
from app.domain.ordered_evaluation import CallForEvaluation, DecisionEvidence, StepDecision, evaluate_step
from app.models import Call, CallStep


def test_required_steps_copies_only_domain_safe_rule_fields():
    steps = required_steps({"steps": [{"key": "greet", "points": 5, "name": "Greet", "done_when": "Say hello"}]})
    assert steps[0].key == "greet" and steps[0].name == "Greet" and steps[0].done_when == "Say hello"


def test_severity_is_derived_from_lost_points_not_full_step_value():
    assert [severity(value) for value in (0, 1, 5, 6, 10, 11, 20, 21)] == [
        "none", "slip", "slip", "inaccuracy", "inaccuracy", "mistake", "mistake", "critical"
    ]


def test_required_steps_preserves_sub_checks_for_python_judgment():
    steps = required_steps({"steps": [{
        "key": "submit", "points": 55, "sub_checks": [{
            "key": "read_back", "type": "read_back_matches_request", "points": 5, "fields": ["amount"],
        }],
    }]})
    assert steps[0].kind == "confirmation"
    assert steps[0].checks[0].fields == ("amount",)


def test_required_steps_normalizes_a_singular_system_record_field():
    steps = required_steps({"steps": [{
        "key": "state_balance", "points": 50, "sub_checks": [{
            "key": "balance", "type": "stated_matches_system_record", "points": 50, "field": "account_balance",
        }],
    }]})
    assert steps[0].checks[0].fields == ("account_balance",)


class Result:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self.rows

    def first(self):
        return next(iter(self.rows), None)

    def all(self):
        return self.rows


class Session:
    def __init__(self, call, rows):
        self.call = call
        self.rows = rows
        self.answers = []

    async def get(self, model, call_id):
        assert model is Call and call_id == self.call.id
        return self.call

    async def execute(self, query):
        return Result(self.answers.pop(0) if self.answers else list(self.rows))

    def add(self, row):
        self.rows.append(row)


@pytest.mark.parametrize("existing", [True, False])
def test_saved_evaluation_round_trips_through_the_get_handler(existing):
    rules = {"steps": [{
        "key": "submit", "name": "Submit", "description": "Log the caller's account", "points": 100,
        "sub_checks": [
            {"key": "type", "type": "logged_task_type", "description": "Correct task", "points": 20,
             "expected": "transfer_money"},
            {"key": "logged", "type": "logged_matches_request", "description": "Correct account", "points": 80,
             "fields": ["transfer_source_account"]},
        ],
    }]}
    required = required_steps(rules)
    call = Call(id=7, external_id="demo", call_type="transfer_money", summary="Obsolete seed summary")
    row = CallStep(call_id=7, step_key="submit", position=1, name="Submit", points=100,
                   detail="Obsolete seed explanation", coaching="Obsolete coaching",
                   comparison=[{"field": "transfer_destination_account", "caller_asked": "stale",
                                "logged": "stale", "match": True}])
    session = Session(call, [row] if existing else [])
    store = SqlAlchemyOrderedCallStore(session)
    evaluation = CallForEvaluation(7, required, {9: "Read back"}, (9,),
                                    {"task_type": "transfer money", "transfer_source_account": "savings"})
    decision = StepDecision("completed_step", .95, DecisionEvidence(9, "Read back"),
                            facts={"request:transfer_source_account": "checking"})
    wrong = evaluate_step(required[0], decision, True, evaluation)
    asyncio.run(store.save_evaluation(evaluation, (wrong,)))
    row = session.rows[0]
    session.answers = [
        [Row(id=7, external_id="demo", call_type="transfer_money", call_type_name="Transfer money",
             summary=call.summary, rules=rules)],
        [Row(idx=9, speaker="agent", start_seconds=None, text="Read back")], [row],
    ]
    out = asyncio.run(get_call_detail(7, GetCallDetail(SqlAlchemyCallDetailReader(session))))
    assert [(check.key, check.description, check.points, check.result) for check in out.steps[0].details.sub_checks] == [
        ("type", "Correct task", 20, "passed"), ("logged", "Correct account", 80, "failed"),
    ]
    assert [(item.field, item.caller_asked, item.logged, item.result) for item in out.type_details.fields] == [
        ("transfer_source_account", "checking", "savings", "mismatch"),
    ]
    assert (out.steps[0].status, out.score.points_lost, out.score.score, call.score) == ("wrong", 80, 20, 20)
    assert row.detail != "Obsolete seed explanation" and row.coaching is None and call.summary is None
    assert out.steps[0].details.evidence.turn_idx == 9

    # Repeat with unresolved request evidence, proving replacement clears the old comparison.
    unresolved = evaluate_step(required[0], StepDecision("unclear", .18), False, evaluation)
    asyncio.run(store.save_evaluation(evaluation, (unresolved,)))
    assert row.comparison is None and row.evidence_turn_idx is None and row.detail is None
    assert row.sub_checks[1]["status"] == "under_review"
    assert (call.status, call.score) == ("needs_review", None)


def test_load_keeps_system_records_private_and_separate_from_logged_values():
    call = Row(id=7, raw_metadata={
        "agent": {"responses": [{"data": {"task type": "check balance", "balance check account type": "savings"}}]},
        "tasks": [{"account balance": "114", "balance check account type": "checking"}],
    }, rules={"fields": [
        {"key": "account_balance", "type": "amount", "role": "told_to_caller", "reference": "system_record",
         "system_record": {"dataset_metadata_key": "account balance"}},
        {"key": "balance_check_account_type", "type": "account", "role": "logged", "reference": "caller_request"},
    ]})
    session = Session(call, [])
    session.answers = [[call], [Row(idx=1, speaker="agent", text="Your balance is 114")]]
    loaded = asyncio.run(SqlAlchemyOrderedCallStore(session).load_for_evaluation(7))
    assert loaded.system_record == {"account_balance": "114"}
    assert loaded.logged_actions == {"task_type": "check balance", "balance_check_account_type": "savings"}
    assert loaded.field_types == {"account_balance": "amount", "balance_check_account_type": "account"}
