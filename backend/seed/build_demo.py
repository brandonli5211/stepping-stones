"""Build the #33 demo dataset.

Combines the hand-written step results (demo_calls.csv) and the step lists
(procedures.json) with real HarperValleyBank calls, and writes demo_calls.json
for `uv run seed` (#29). The HarperValleyBank files are only read, never changed.

Usage (from backend/):
    python seed/build_demo.py --hvb ~/gridspace-stanford-harper-valley/data
"""

import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE_DATE = "2026-10-09"  # "this week" is the week of this date, so the demo never shifts


def severity(points: int) -> str:
    """#29 rule: up to 5 slip, 6-10 inaccuracy, 11-20 mistake, over 20 critical."""
    if points <= 5:
        return "slip"
    if points <= 10:
        return "inaccuracy"
    if points <= 20:
        return "mistake"
    return "critical"


def split(cell: str) -> list[str]:
    return [s for s in cell.split(";") if s]


def load_turns(hvb: Path, call_id: str) -> list[dict] | None:
    """Every turn exactly as in the dataset, noise included. The app filters and sorts."""
    path = hvb / "transcript" / f"{call_id}.json"
    if not path.exists():
        return None
    return [
        {
            "speaker": t["speaker_role"],
            "start_ms": t["start_ms"],
            "duration_ms": t["duration_ms"],
            "text": t["human_transcript"],
        }
        for t in json.loads(path.read_text())
    ]


def transfer_table(meta: dict) -> list[dict]:
    """Caller asked vs logged, read straight from the dataset's metadata."""
    asked = meta["tasks"][0]
    logged = meta["agent"]["responses"][-1]["data"] if meta["agent"].get("responses") else {}
    rows = []
    for label, key in [("Amount", "transfer amount"), ("From", "transfer source account"),
                       ("To", "transfer destination account")]:
        a, l = asked.get(key), logged.get(key)
        rows.append({"field": label, "caller_asked": a, "logged": l,
                     "result": "match" if str(a) == str(l) else "mismatch"})
    return rows


def build(hvb: Path) -> dict:
    procedures = json.loads((HERE / "procedures.json").read_text())
    evidence = json.loads((HERE / "evidence.json").read_text())
    calls = []
    with open(HERE / "demo_calls.csv", newline="") as f:
        for row in csv.DictReader(f):
            call_type = row["call_type"]
            steps_def = procedures[call_type]
            ids = [s["id"] for s in steps_def]
            missed, wrong = split(row["missed_steps"]), split(row["wrong_steps"])
            for s in missed + wrong:
                if s not in ids:
                    raise ValueError(f"{row['demo_id']}: unknown step '{s}' for {call_type}")

            notes = evidence.get(row["hvb_call_id"], [])
            steps, flags = [], []
            for s in steps_def:
                status = "wrong" if s["id"] in wrong else "missed" if s["id"] in missed else "completed"
                lost = 0 if status == "completed" else s["points"]
                quote = next((n for n in notes if n["step_id"] == s["id"] and n.get("quote")), None)
                steps.append({"step_id": s["id"], "status": status, "points_lost": lost,
                              "quote_start_ms": quote["start_ms"] if quote else None})
                if lost:
                    flags.append({"step_id": s["id"], "severity": severity(lost), "points_lost": lost})

            meta = json.loads((hvb / "metadata" / f"{row['hvb_call_id']}.json").read_text())
            if meta["tasks"][0]["task_type"] != call_type:
                raise ValueError(f"{row['demo_id']}: {row['hvb_call_id']} is not a {call_type} call")

            calls.append({
                "id": row["demo_id"],
                "hvb_call_id": row["hvb_call_id"],
                "call_type": call_type,
                "started_at": f"{row['date']}T{row['time']}:00",
                "source": "demo",
                "steps": steps,
                "flags": flags,
                "notes": [{k: n[k] for k in ("start_ms", "step_id", "kind", "text")} for n in notes],
                "transcript": load_turns(hvb, row["hvb_call_id"]),
                "type_details": {"caller_asked_vs_logged": transfer_table(meta)}
                if call_type == "transfer money" else {},
            })
    return {"reference_date": REFERENCE_DATE, "source": "demo",
            "procedures": procedures, "calls": calls}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hvb", required=True, type=Path,
                        help="HarperValleyBank data folder (the one holding metadata/ and transcript/)")
    parser.add_argument("--out", type=Path, default=HERE / "demo_calls.json")
    args = parser.parse_args()
    data = build(args.hvb.expanduser())
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(data['calls'])} calls to {args.out}")


if __name__ == "__main__":
    main()
