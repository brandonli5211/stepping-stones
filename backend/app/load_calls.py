"""Read every transcript + metadata pair in a folder and insert them with plain SQL.

    uv run python -m app.load_calls <folder with transcript/ and metadata/> [--spread-days 42] [--demo-results]

Fills: procedures (from docs/procedures/schema3), agents, calls, call_turns. Uses DATABASE_URL.
Run it again any time: procedures are updated, calls already loaded (same external_id) are skipped.

By default only what is in the files is stored: calls are inserted with status 'pending' (no score, no steps).
--demo-results also fills call_steps and the score from simple rules, WITHOUT a model (see call_parse.seed_steps):
only the logged values are compared with the assigned task and the other steps are assumed done. Those calls get
model = 'demo-seed' so they can be told apart from real analysis. Do not use it on real data.
--spread-days moves call dates into the last N days (the dataset's own dates are from 2020, so GET /calls?weeks=8
would otherwise return nothing).
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from app.call_parse import parse_call, seed_steps

DEFAULT_RULES = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"

UPSERT_PROCEDURE = """
INSERT INTO procedures (call_type, version, name, rules, is_active)
VALUES (%s, %s, %s, %s, true)
ON CONFLICT (call_type, version) DO UPDATE SET name = EXCLUDED.name, rules = EXCLUDED.rules
RETURNING id
"""
FIND_AGENT = "SELECT id FROM agents WHERE name = %s ORDER BY id LIMIT 1"
INSERT_AGENT = "INSERT INTO agents (name) VALUES (%s) RETURNING id"
INSERT_CALL_PENDING = """
INSERT INTO calls (external_id, agent_id, call_type, procedure_id, started_at, raw_metadata, raw_transcript)
VALUES (%s, %s, %s, %s, COALESCE(%s, now()), %s, %s)
ON CONFLICT (external_id) DO NOTHING
RETURNING id
"""
INSERT_CALL_DEMO = """
INSERT INTO calls (external_id, agent_id, call_type, procedure_id, started_at, status, score, points_lost,
                   steps_total, steps_completed, steps_missed, steps_wrong, steps_under_review,
                   raw_metadata, raw_transcript, model, prompt_version, analyzed_at)
VALUES (%s, %s, %s, %s, COALESCE(%s, now()), 'scored', %s, %s, %s, %s, %s, %s, %s, %s, %s, 'demo-seed', 'seed-v1', now())
ON CONFLICT (external_id) DO NOTHING
RETURNING id
"""
INSERT_TURN = """
INSERT INTO call_turns (call_id, idx, speaker, start_seconds, text, machine_text)
VALUES (%s, %s, %s, %s, %s, %s)
"""
INSERT_STEP = """
INSERT INTO call_steps (call_id, step_key, position, name, points, status, severity, points_lost,
                        points_under_review, detail, sub_checks, comparison)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def read_pairs(folder: Path) -> list[dict]:
    """Parse every metadata/<sid>.json with its transcript/<sid>.json. Oldest call first."""
    calls = []
    for meta_path in sorted((folder / "metadata").glob("*.json")):
        transcript_path = folder / "transcript" / meta_path.name
        if transcript_path.is_file():
            calls.append(parse_call(json.loads(transcript_path.read_text(encoding="utf-8")),
                                    json.loads(meta_path.read_text(encoding="utf-8"))))
    calls.sort(key=lambda c: c["started_at"] or datetime.min.replace(tzinfo=timezone.utc))
    return calls


def spread_dates(calls: list[dict], days: int) -> None:
    """Newest call = now, oldest = `days` ago, the rest evenly between."""
    now = datetime.now(timezone.utc)
    for i, c in enumerate(calls):
        c["started_at"] = now - timedelta(days=days * (len(calls) - 1 - i) / max(len(calls) - 1, 1))


def load(conn, folder: Path, rules_dir: Path = DEFAULT_RULES, spread_days: int | None = None, demo_results: bool = False) -> dict:
    """Insert everything through `conn` (a psycopg connection). The caller commits."""
    common = json.loads((rules_dir / "_common.json").read_text(encoding="utf-8"))
    counts = {"loaded": 0, "skipped_existing": 0, "skipped_no_procedure": 0}
    with conn.cursor() as cur:
        procedures = {}  # call_type -> (id, rules)
        for path in sorted(rules_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            cur.execute(UPSERT_PROCEDURE, (doc["call_type"], doc["version"], doc["name"], Jsonb(doc)))
            procedures[doc["call_type"]] = (cur.fetchone()[0], doc)

        calls = read_pairs(folder)
        if spread_days:
            spread_dates(calls, spread_days)

        agents = {}
        for c in calls:
            if c["call_type"] not in procedures:
                counts["skipped_no_procedure"] += 1
                continue
            if c["agent_name"] not in agents:
                cur.execute(FIND_AGENT, (c["agent_name"],))
                row = cur.fetchone()
                if row is None:
                    cur.execute(INSERT_AGENT, (c["agent_name"],))
                    row = cur.fetchone()
                agents[c["agent_name"]] = row[0]

            procedure_id, rules = procedures[c["call_type"]]
            r = seed_steps(rules, common, c) if demo_results else None
            if r:
                cur.execute(INSERT_CALL_DEMO, (
                    c["external_id"], agents[c["agent_name"]], c["call_type"], procedure_id, c["started_at"],
                    r["score"], r["points_lost"], len(r["steps"]), r["completed"], r["missed"], r["wrong"], r["under_review"],
                    Jsonb(c["raw_metadata"]), Jsonb(c["raw_transcript"]),
                ))
            else:
                cur.execute(INSERT_CALL_PENDING, (
                    c["external_id"], agents[c["agent_name"]], c["call_type"], procedure_id, c["started_at"],
                    Jsonb(c["raw_metadata"]), Jsonb(c["raw_transcript"]),
                ))
            row = cur.fetchone()
            if row is None:  # already loaded
                counts["skipped_existing"] += 1
                continue
            call_id = row[0]
            cur.executemany(INSERT_TURN, [
                (call_id, t["idx"], t["speaker"], t["start_seconds"], t["text"], t["machine_text"]) for t in c["turns"]])
            if r:
                cur.executemany(INSERT_STEP, [
                    (call_id, s["step_key"], s["position"], s["name"], s["points"], s["status"], s["severity"], s["points_lost"],
                     s["points_under_review"], s["detail"], Jsonb(s["sub_checks"]),
                     None if s["comparison"] is None else Jsonb(s["comparison"])) for s in r["steps"]])
            counts["loaded"] += 1
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path, help="folder that contains transcript/ and metadata/")
    ap.add_argument("--rules-dir", type=Path, default=DEFAULT_RULES)
    ap.add_argument("--demo-results", action="store_true", help="also fill step results and score with demo rules (no model)")
    ap.add_argument("--spread-days", type=int, help="spread the call dates over the last N days")
    args = ap.parse_args()
    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url) as conn:  # commits on success, rolls back on error
        print(load(conn, args.folder, args.rules_dir, args.spread_days, args.demo_results))


if __name__ == "__main__":
    main()
