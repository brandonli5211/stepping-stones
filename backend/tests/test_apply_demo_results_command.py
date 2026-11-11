import asyncio
from pathlib import Path

import pytest

from app.adapters.persistence.demo_call_store import FIND_CALLS, UPDATE_CALL
from app.application.apply_demo_results import ApplyOutcome
from app.adapters.persistence.engine import get_session
from app.infrastructure.apply_demo_results import DEFAULT_RULES, _apply_with_database, apply_with_session, main

_REPO = Path(__file__).resolve().parents[2]
HEADER = "demo_id,hvb_call_id,call_type,date,time,missed_steps,wrong_steps\n"


def write_csv(tmp_path, body="D1,abc,pay_bill,2026-10-01,09:15,,\n", header=HEADER):
    path = tmp_path / "results.csv"
    path.write_text(header + body, encoding="utf-8")
    return path


def runner(outcome, seen):
    async def run(rows, bands):
        seen.append((rows, bands))
        return outcome
    return run


def test_default_rules_dir_is_schema3():
    assert DEFAULT_RULES == _REPO / "docs" / "procedures" / "schema3"
    assert (DEFAULT_RULES / "_common.json").is_file()


def test_saved_outcome_exits_zero_and_prints_summary(tmp_path, capsys):
    seen = []
    code = main([str(write_csv(tmp_path))], run_use_case=runner(ApplyOutcome(1, (), True), seen))
    assert code == 0
    assert capsys.readouterr().out.strip() == "{'updated': 1, 'problems': [], 'saved': True}"
    rows, bands = seen[0]
    assert [r.external_id for r in rows] == ["abc"]
    assert [b.name for b in bands] == ["slip", "inaccuracy", "mistake", "critical"]


def test_problem_outcome_exits_one_and_prints_problems(tmp_path, capsys):
    outcome = ApplyOutcome(0, ("D1: call not loaded",), False)
    code = main([str(write_csv(tmp_path))], run_use_case=runner(outcome, []))
    assert code == 1
    assert "D1: call not loaded" in capsys.readouterr().out


def test_missing_column_exits_one_without_running_use_case(tmp_path, capsys):
    seen = []
    path = write_csv(tmp_path, body="D1,abc\n", header="demo_id,hvb_call_id\n")
    assert main([str(path)], run_use_case=runner(ApplyOutcome(0, (), True), seen)) == 1
    assert seen == []
    assert "missing column(s)" in capsys.readouterr().out


def test_missing_file_exits_one(tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv")], run_use_case=runner(ApplyOutcome(0, (), True), [])) == 1
    assert "error:" in capsys.readouterr().out


class _Transaction:
    def __init__(self, log):
        self.log = log

    async def __aenter__(self):
        self.log.append("begin")

    async def __aexit__(self, exc_type, exc, tb):
        self.log.append("rollback" if exc_type else "commit")
        return False


class _Result:
    def __init__(self, rows=(), scalar=None):
        self._rows, self._scalar = list(rows), scalar

    def all(self):
        return self._rows

    def scalar_one(self):
        return self._scalar


class FakeSession:
    def __init__(self, fail_on_update=False):
        self.log = []
        self.fail_on_update = fail_on_update

    def begin(self):
        return _Transaction(self.log)

    async def execute(self, stmt, params=None):
        self.log.append("find" if stmt is FIND_CALLS else "update_call" if stmt is UPDATE_CALL else "update_step")
        if stmt is FIND_CALLS:
            return _Result(rows=[("abc", "pay_bill", "greet", "Greet", 5, "completed", None)])
        if self.fail_on_update:
            raise RuntimeError("database error")
        return _Result(scalar=1)


def _rows(tmp_path):
    from app.adapters.files.demo_results_files import read_results_csv, read_severity_bands
    return read_results_csv(write_csv(tmp_path)), read_severity_bands(DEFAULT_RULES)


def test_apply_with_session_wraps_read_and_writes_in_one_transaction(tmp_path):
    session = FakeSession()
    rows, bands = _rows(tmp_path)
    outcome = asyncio.run(apply_with_session(session, rows, bands))
    assert outcome == ApplyOutcome(1, (), True)
    assert session.log == ["begin", "find", "update_call", "update_step", "commit"]


def test_apply_with_session_rolls_back_and_propagates_on_error(tmp_path):
    session = FakeSession(fail_on_update=True)
    rows, bands = _rows(tmp_path)
    with pytest.raises(RuntimeError, match="database error"):
        asyncio.run(apply_with_session(session, rows, bands))
    assert session.log == ["begin", "find", "update_call", "rollback"]


class FakeSessionSource:
    def __init__(self, session):
        self.session = session
        self.closed = False

    def __call__(self):
        async def source():
            try:
                yield self.session
            finally:
                self.closed = True
        return source()


def test_apply_with_database_defaults_to_engine_get_session():
    assert _apply_with_database.__defaults__ == (get_session,)


def test_apply_with_database_runs_on_yielded_session_and_closes_source(tmp_path):
    session = FakeSession()
    source = FakeSessionSource(session)
    rows, bands = _rows(tmp_path)
    outcome = asyncio.run(_apply_with_database(rows, bands, session_source=source))
    assert outcome == ApplyOutcome(1, (), True)
    assert session.log == ["begin", "find", "update_call", "update_step", "commit"]
    assert source.closed is True


def test_apply_with_database_closes_source_on_error(tmp_path):
    session = FakeSession(fail_on_update=True)
    source = FakeSessionSource(session)
    rows, bands = _rows(tmp_path)
    with pytest.raises(RuntimeError, match="database error"):
        asyncio.run(_apply_with_database(rows, bands, session_source=source))
    assert session.log[-1] == "rollback"
    assert source.closed is True
