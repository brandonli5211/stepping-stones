"""Read the demo results CSV and the schema3 severity bands into domain types."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from app.domain.demo_results import ResultsRow, SeverityBand, parse_step_keys

REQUIRED_COLUMNS = ("demo_id", "hvb_call_id", "call_type", "date", "time", "missed_steps", "wrong_steps")


def _optional(r: dict, column: str) -> str:
    """A missing column or a short row gives ""."""
    return (r.get(column) or "").strip()


def read_results_csv(path: Path) -> list[ResultsRow]:
    """One ResultsRow per CSV row. Raises ValueError naming any missing required column.

    The evidence columns are optional and are read as raw stripped strings; the domain validates them.
    """
    with Path(path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing column(s) {', '.join(missing)}")
        return [
            ResultsRow(
                demo_id=r["demo_id"].strip(),
                external_id=r["hvb_call_id"].strip(),
                call_type=r["call_type"].strip(),
                date=r["date"].strip(),
                time=r["time"].strip(),
                missed=parse_step_keys(r["missed_steps"]),
                wrong=parse_step_keys(r["wrong_steps"]),
                evidence_step=_optional(r, "evidence_step"),
                evidence_turn=_optional(r, "evidence_turn"),
                evidence_quote=_optional(r, "evidence_quote"),
            )
            for r in reader
        ]


def read_severity_bands(rules_dir: Path) -> tuple[SeverityBand, ...]:
    """The severity bands from <rules_dir>/_common.json (severity.bands)."""
    common = json.loads((Path(rules_dir) / "_common.json").read_text(encoding="utf-8"))
    return tuple(
        SeverityBand(b["name"], b["min_points_lost"], b["max_points_lost"]) for b in common["severity"]["bands"]
    )
