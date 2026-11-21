import asyncio
from decimal import Decimal
from types import SimpleNamespace as Row

import pytest

from app.adapters.persistence.call_detail_reader import (
    SqlAlchemyCallDetailReader,
    _text,
    step_descriptions,
    to_call_record,
    to_comparison_row,
    to_step_record,
    to_sub_check,
    to_turn_record,
)
from app.domain.call_detail import CallRecord, ComparisonRow, InvalidCallRecord, SubCheck, TurnRecord


def _step_row(**overrides):
    values = dict(
        step_key="submit_and_confirm_transfer", position=5, name="Submit and confirm transfer", points=55,
        status="wrong", severity="critical", points_lost=55, points_under_review=0, detail="read back reversed",
        evidence_turn_idx=9, evidence_quote="from your savings", coaching="Next time ...",
        sub_checks=[{"key": "read_back", "description": "Read back", "points": 15, "status": "failed"}],
        comparison=[{"field": "transfer_amount", "caller_asked": 114, "logged": "114", "match": True}],
    )
    values.update(overrides)
    return Row(**values)


RULES = {"steps": [{"key": "submit_and_confirm_transfer", "description": "Log the transfer correctly."},
                   {"key": "close"}]}


def _call_row():
    return Row(id=6, external_id="a2f086d27b3a4f96", call_type="transfer_money", call_type_name="Transfer money",
               summary="One sentence.", rules=RULES)


def test_text_keeps_none_and_turns_values_into_text():
    assert _text(None) is None
    assert _text(114) == "114"


def test_step_descriptions_maps_keys_to_descriptions():
    assert step_descriptions(RULES) == {"submit_and_confirm_transfer": "Log the transfer correctly."}


def test_step_descriptions_handles_missing_rules():
    assert step_descriptions(None) == {}
    assert step_descriptions({"steps": ["not a step"]}) == {}


def test_to_step_record_takes_the_description():
    assert to_step_record(_step_row(), "Log the transfer correctly.").description == "Log the transfer correctly."
    assert to_step_record(_step_row()).description is None


def test_to_turn_record_converts_the_stored_time():
    assert to_turn_record(Row(idx=9, speaker="agent", start_seconds=Decimal("33.53"), text="okay")) == \
        TurnRecord(9, "agent", 33.53, "okay")


def test_to_turn_record_keeps_a_missing_time():
    assert to_turn_record(Row(idx=1, speaker="caller", start_seconds=None, text="hi")).start_seconds is None


def test_to_sub_check_reads_the_stored_status_as_the_result():
    assert to_sub_check({"key": "k", "description": "d", "points": 5, "status": "passed"}) == SubCheck("k", "d", 5, "passed")
    assert to_sub_check({"key": "k"}) == SubCheck("k", "", 0, "under_review")


def test_to_comparison_row_turns_values_into_text():
    assert to_comparison_row({"field": "transfer_amount", "caller_asked": 114, "logged": None, "match": False}) == \
        ComparisonRow("transfer_amount", "114", None, False)


def test_to_step_record_maps_every_column():
    step = to_step_record(_step_row())
    assert (step.key, step.position, step.status, step.severity, step.points_lost) == \
        ("submit_and_confirm_transfer", 5, "wrong", "critical", 55)
    assert step.sub_checks == (SubCheck("read_back", "Read back", 15, "failed"),)
    assert step.comparison == (ComparisonRow("transfer_amount", "114", "114", True),)
    assert (step.evidence_turn_idx, step.evidence_quote, step.coaching) == (9, "from your savings", "Next time ...")


def test_to_step_record_handles_empty_json_columns():
    step = to_step_record(_step_row(sub_checks=[], comparison=None, status="completed", severity="none",
                                    points_lost=0, detail=None))
    assert step.sub_checks == () and step.comparison == ()


def test_to_call_record_builds_the_whole_record():
    record = to_call_record(_call_row(), [Row(idx=1, speaker="agent", start_seconds=None, text="hi")], [_step_row()])
    assert isinstance(record, CallRecord)
    assert (record.id, record.call_type_name, record.summary) == (6, "Transfer money", "One sentence.")
    assert len(record.turns) == 1 and len(record.steps) == 1
    assert record.steps[0].description == "Log the transfer correctly."


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return list(self._rows)


class _StubSession:
    """Answers the reader's queries in order and records that nothing was written."""

    def __init__(self, *answers):
        self._answers = list(answers)
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _Result(self._answers.pop(0))


def test_reader_get_returns_the_call_with_its_turns_and_steps():
    session = _StubSession([_call_row()], [Row(idx=1, speaker="agent", start_seconds=Decimal("2.30"), text="hi")],
                           [_step_row()])
    record = asyncio.run(SqlAlchemyCallDetailReader(session).get(6))
    assert record.id == 6
    assert record.turns[0].start_seconds == 2.3
    assert record.steps[0].key == "submit_and_confirm_transfer"
    assert len(session.statements) == 3
    assert all(str(s).lstrip().upper().startswith("SELECT") for s in session.statements)


def test_reader_get_names_the_call_when_stored_data_is_invalid():
    bad_step = _step_row(sub_checks=[{"key": "read_back", "points": 15, "status": "skipped"}])
    session = _StubSession([_call_row()], [], [bad_step])
    with pytest.raises(InvalidCallRecord, match=r"call 6: sub-check read_back result is 'skipped'"):
        asyncio.run(SqlAlchemyCallDetailReader(session).get(6))


def test_reader_get_returns_none_for_an_unknown_call():
    session = _StubSession([])
    assert asyncio.run(SqlAlchemyCallDetailReader(session).get(999999)) is None
    assert len(session.statements) == 1
