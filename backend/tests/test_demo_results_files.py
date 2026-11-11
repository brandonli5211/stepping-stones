from pathlib import Path

import pytest

from app.adapters.files.demo_results_files import read_results_csv, read_severity_bands
from app.domain.demo_results import ResultsRow, SeverityBand

_REPO = Path(__file__).resolve().parents[2]


def test_read_results_csv_round_trip(tmp_path):
    path = tmp_path / "r.csv"
    path.write_text(
        "demo_id,hvb_call_id,call_type,date,time,missed_steps,wrong_steps,extra\n"
        "D1,abc,pay_bill,2026-10-01,09:15, a; b ,,ignored\n"
        "D2,def,check_balance,2026-10-02,10:00,,c\n",
        encoding="utf-8",
    )
    assert read_results_csv(path) == [
        ResultsRow("D1", "abc", "pay_bill", "2026-10-01", "09:15", frozenset({"a", "b"}), frozenset()),
        ResultsRow("D2", "def", "check_balance", "2026-10-02", "10:00", frozenset(), frozenset({"c"})),
    ]


def test_read_results_csv_missing_columns_raise(tmp_path):
    path = tmp_path / "r.csv"
    path.write_text("demo_id,hvb_call_id,date,time,missed_steps\nD1,abc,2026-10-01,09:15,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="call_type, wrong_steps"):
        read_results_csv(path)


def test_read_results_csv_real_demo_file():
    rows = read_results_csv(_REPO / "sample" / "demo_48" / "results.csv")
    assert len(rows) == 48
    demo06 = next(r for r in rows if r.demo_id == "HVB-DEMO-06")
    assert demo06.external_id == "a2f086d27b3a4f96"
    assert demo06.wrong == frozenset({"submit_and_confirm_transfer"})
    assert demo06.missed == frozenset()


def test_read_severity_bands_real_rules():
    assert read_severity_bands(_REPO / "docs" / "procedures" / "schema3") == (
        SeverityBand("slip", 1, 5),
        SeverityBand("inaccuracy", 6, 10),
        SeverityBand("mistake", 11, 20),
        SeverityBand("critical", 21, None),
    )
