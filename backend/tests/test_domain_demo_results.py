import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import app.domain.demo_results as demo_results
from app.call_parse import _band
from app.domain.demo_results import (
    ResultsRow,
    ScoredStep,
    SeverityBand,
    StoredCall,
    StoredStep,
    duplicate_problems,
    parse_step_keys,
    row_problems,
    score_call,
    severity_for,
    toronto_start,
)

_COMMON = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3" / "_common.json"

BANDS = (
    SeverityBand("slip", 1, 5),
    SeverityBand("inaccuracy", 6, 10),
    SeverityBand("mistake", 11, 20),
    SeverityBand("critical", 21, None),
)

TRANSFER = StoredCall(
    external_id="a2f086d27b3a4f96",
    call_type="transfer_money",
    steps=(
        StoredStep("greet_and_open", "Greet and open", 5, "completed", None),
        StoredStep("collect_transfer_amount", "Collect transfer amount", 10, "completed", None),
        StoredStep("collect_source_account", "Collect source account", 10, "completed", None),
        StoredStep("collect_destination_account", "Collect destination account", 10, "completed", None),
        StoredStep("submit_and_confirm_transfer", "Submit and confirm transfer", 55, "under_review", "seed note"),
        StoredStep("offer_further_help", "Offer further help", 5, "completed", "kept"),
        StoredStep("close", "Close", 5, "completed", None),
    ),
)


def row(missed="", wrong="", *, demo_id="HVB-DEMO-06", external_id="a2f086d27b3a4f96",
        call_type="transfer_money", date="2026-10-07", time="16:48"):
    return ResultsRow(demo_id, external_id, call_type, date, time, parse_step_keys(missed), parse_step_keys(wrong))


# parse_step_keys

def test_parse_step_keys_splits_trims_and_drops_empty_items():
    assert parse_step_keys(" a; b;;c ;") == frozenset({"a", "b", "c"})


def test_parse_step_keys_empty_or_none_is_empty_set():
    assert parse_step_keys("") == frozenset()
    assert parse_step_keys(None) == frozenset()


# toronto_start

def test_toronto_start_daylight_time_is_utc_minus_four():
    assert toronto_start("2026-10-07", "16:48") == datetime(2026, 10, 7, 20, 48, tzinfo=timezone.utc)


def test_toronto_start_standard_time_is_utc_minus_five():
    assert toronto_start("2026-01-15", "09:00") == datetime(2026, 1, 15, 14, 0, tzinfo=timezone.utc)


def test_toronto_start_late_evening_rolls_to_next_utc_day():
    assert toronto_start("2026-10-09", "22:30") == datetime(2026, 10, 10, 2, 30, tzinfo=timezone.utc)


@pytest.mark.parametrize("date,time", [("2026-13-01", "10:00"), ("2026-10-07", "25:00"), ("", ""), ("2026/10/07", "10:00")])
def test_toronto_start_rejects_malformed_values(date, time):
    with pytest.raises(ValueError):
        toronto_start(date, time)


# severity_for

@pytest.mark.parametrize("lost,expected", [
    (-3, "none"), (0, "none"), (1, "slip"), (5, "slip"), (6, "inaccuracy"), (10, "inaccuracy"),
    (11, "mistake"), (20, "mistake"), (21, "critical"), (55, "critical"), (100, "critical"),
])
def test_severity_for_band_boundaries(lost, expected):
    assert severity_for(BANDS, lost) == expected


def test_severity_for_above_all_closed_bands_uses_last_band():
    assert severity_for((SeverityBand("small", 1, 5), SeverityBand("big", 6, 10)), 50) == "big"


def test_severity_for_matches_call_parse_band_on_real_rules():
    common = json.loads(_COMMON.read_text(encoding="utf-8"))
    bands = tuple(SeverityBand(b["name"], b["min_points_lost"], b["max_points_lost"]) for b in common["severity"]["bands"])
    for lost in range(0, 101):
        assert severity_for(bands, lost) == _band(common, lost)


# duplicate_problems

def test_duplicate_problems_none_for_distinct_calls():
    assert duplicate_problems([row(external_id="a"), row(external_id="b")]) == []


def test_duplicate_problems_flags_every_repeat_in_file_order():
    rows = [row(demo_id="D1", external_id="x"), row(demo_id="D2", external_id="y"),
            row(demo_id="D3", external_id="x"), row(demo_id="D4", external_id="x")]
    assert duplicate_problems(rows) == ["D3: call x listed more than once", "D4: call x listed more than once"]


# row_problems

def test_row_problems_valid_row_is_empty():
    assert row_problems(row(wrong="submit_and_confirm_transfer"), TRANSFER) == []


def test_row_problems_missing_call_is_only_problem():
    assert row_problems(row(wrong="nope", call_type="other", date="bad"), None) == ["HVB-DEMO-06: call not loaded"]


def test_row_problems_call_without_steps_skips_unknown_key_check():
    empty = StoredCall("a2f086d27b3a4f96", "transfer_money", ())
    assert row_problems(row(wrong="submit_and_confirm_transfer"), empty) == [
        "HVB-DEMO-06: call has no rubric steps (load with --demo-results)"]


def test_row_problems_call_type_mismatch():
    assert row_problems(row(call_type="pay_bill"), TRANSFER) == [
        "HVB-DEMO-06: call_type pay_bill, loaded call is transfer_money"]


def test_row_problems_unknown_keys_sorted():
    assert row_problems(row(missed="zeta", wrong="alpha"), TRANSFER) == [
        "HVB-DEMO-06: unknown step alpha", "HVB-DEMO-06: unknown step zeta"]


def test_row_problems_key_both_missed_and_wrong():
    assert row_problems(row(missed="close", wrong="close"), TRANSFER) == [
        "HVB-DEMO-06: step close is both missed and wrong"]


def test_row_problems_bad_date_time():
    assert row_problems(row(date="2026-10-32", time="16:48"), TRANSFER) == [
        "HVB-DEMO-06: bad date/time 2026-10-32 16:48"]


def test_row_problems_reports_several_problems_in_order():
    assert row_problems(row(missed="close;bogus", wrong="close", call_type="pay_bill", time="99:99"), TRANSFER) == [
        "HVB-DEMO-06: call_type pay_bill, loaded call is transfer_money",
        "HVB-DEMO-06: unknown step bogus",
        "HVB-DEMO-06: step close is both missed and wrong",
        "HVB-DEMO-06: bad date/time 2026-10-07 99:99",
    ]


# score_call

def test_score_call_worked_example_scores_45():
    scored = score_call(row(wrong="submit_and_confirm_transfer"), TRANSFER, BANDS)
    assert scored.external_id == "a2f086d27b3a4f96"
    assert scored.started_at == datetime(2026, 10, 7, 20, 48, tzinfo=timezone.utc)
    assert (scored.score, scored.points_lost, scored.steps_total) == (45, 55, 7)
    assert (scored.steps_completed, scored.steps_missed, scored.steps_wrong) == (6, 0, 1)
    wrong = [s for s in scored.steps if s.status == "wrong"]
    assert wrong == [ScoredStep("submit_and_confirm_transfer", "wrong", "critical", 55, None)]
    assert all(s.severity == "none" and s.points_lost == 0 for s in scored.steps if s.status == "completed")


def test_score_call_empty_row_scores_100():
    scored = score_call(row(), TRANSFER, BANDS)
    assert (scored.score, scored.points_lost, scored.steps_completed) == (100, 0, 7)


def test_score_call_two_missed_five_point_steps_score_90_with_slip():
    scored = score_call(row(missed="greet_and_open;close"), TRANSFER, BANDS)
    assert scored.score == 90
    assert scored.steps_missed == 2
    missed = {s.key: (s.severity, s.points_lost) for s in scored.steps if s.status == "missed"}
    assert missed == {"greet_and_open": ("slip", 5), "close": ("slip", 5)}


def test_score_call_never_below_zero():
    heavy = StoredCall("x", "t", (StoredStep("a", "A", 70, "completed", None), StoredStep("b", "B", 60, "completed", None)))
    scored = score_call(row(missed="a", wrong="b", external_id="x", call_type="t"), heavy, BANDS)
    assert (scored.score, scored.points_lost) == (0, 130)


def test_score_call_keeps_detail_only_when_status_unchanged():
    scored = {s.key: s for s in score_call(row(), TRANSFER, BANDS).steps}
    assert scored["offer_further_help"].detail == "kept"  # completed -> completed
    assert scored["submit_and_confirm_transfer"].detail is None  # under_review -> completed


# layering

def test_domain_module_imports_no_framework_or_driver():
    tree = ast.parse(Path(demo_results.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint({"fastapi", "sqlalchemy", "alembic", "psycopg", "app"})
