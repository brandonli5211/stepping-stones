import json
from pathlib import Path

from app.call_parse import _band
from app.domain.demo_results import SeverityBand, severity_for

COMMON = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3" / "_common.json"


def test_severity_matches_seed():
    common = json.loads(COMMON.read_text(encoding="utf-8"))
    bands = tuple(SeverityBand(b["name"], b["min_points_lost"], b["max_points_lost"]) for b in common["severity"]["bands"])

    for lost in range(0, 101):
        assert severity_for(bands, lost) == _band(common, lost)
