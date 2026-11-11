"""Overwrite demo call dates and step results from a results CSV.

Usage: uv run python -m app.apply_results ../sample/demo_48/results.csv
"""
import csv
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg

TZ = ZoneInfo("America/Toronto")


def band(lost: int) -> str:
    if lost == 0:
        return "none"
    if lost <= 5:
        return "slip"
    if lost <= 10:
        return "inaccuracy"
    if lost <= 20:
        return "mistake"
    return "critical"


def split(cell: str) -> set[str]:
    return {s.strip() for s in (cell or "").split(";") if s.strip()}


def apply(conn, csv_path: str) -> dict:
    updated, problems = 0, []
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    with conn.cursor() as cur:
        for r in rows:
            cur.execute("SELECT id FROM calls WHERE external_id = %s", (r["hvb_call_id"],))
            hit = cur.fetchone()
            if hit is None:
                problems.append(f"{r['demo_id']}: call not in database")
                continue
            call_id = hit[0]
            missed, wrong = split(r["missed_steps"]), split(r["wrong_steps"])
            cur.execute("SELECT step_key, points FROM call_steps WHERE call_id = %s", (call_id,))
            steps = cur.fetchall()
            for bad in (missed | wrong) - {k for k, _ in steps}:
                problems.append(f"{r['demo_id']}: unknown step {bad}")

            counts = {"completed": 0, "missed": 0, "wrong": 0}
            lost_total = 0
            for key, points in steps:
                status = "missed" if key in missed else "wrong" if key in wrong else "completed"
                lost = 0 if status == "completed" else points
                counts[status] += 1
                lost_total += lost
                cur.execute(
                    """UPDATE call_steps
                       SET status = %s, severity = %s, points_lost = %s, points_under_review = 0,
                           detail = CASE WHEN status = %s THEN detail ELSE NULL END
                       WHERE call_id = %s AND step_key = %s""",
                    (status, band(lost), lost, status, call_id, key),
                )

            started = datetime.strptime(f"{r['date']} {r['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
            cur.execute(
                """UPDATE calls
                   SET started_at = %s, status = 'scored', score = %s, points_lost = %s,
                       steps_total = %s, steps_completed = %s, steps_missed = %s,
                       steps_wrong = %s, steps_under_review = 0
                   WHERE id = %s""",
                (started, max(0, 100 - lost_total), lost_total, len(steps),
                 counts["completed"], counts["missed"], counts["wrong"], call_id),
            )
            updated += 1

    if problems:
        conn.rollback()
        return {"updated": 0, "problems": problems, "saved": False}
    conn.commit()
    return {"updated": updated, "problems": [], "saved": True}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python -m app.apply_results <results.csv>")
    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn:
        result = apply(conn, sys.argv[1])
    print(result)
    if result["problems"]:
        sys.exit(1)


if __name__ == "__main__":
    main()