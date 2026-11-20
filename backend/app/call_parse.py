"""Turn one call's transcript file and metadata file (HarperValleyBank format) into plain dicts ready to insert.

No database code here. Metadata keys use spaces ("transfer amount"); procedures use snake_case, so keys are converted.
"""

import re
from datetime import datetime, timezone
from typing import Any


def snake(text: Any) -> str:
    return "_".join(str(text).strip().lower().split())


def parse_call(transcript: list[dict], metadata: dict) -> dict:
    agent = metadata.get("agent") or {}
    submissions = [r for r in agent.get("responses") or [] if r.get("data")]
    logged = {snake(k): v for k, v in (submissions[-1]["data"] if submissions else {}).items()}  # last submission counts
    logged_type = logged.pop("task_type", None)
    assigned = {snake(k): v for k, v in ((metadata.get("tasks") or [{}])[0]).items()}
    assigned_type = assigned.pop("task_type", None)

    turns = []
    for i, t in enumerate(transcript, 1):
        human = (t.get("human_transcript") or "").strip()
        machine = (t.get("transcript") or "").strip()
        start_ms = t.get("start_ms")
        turns.append({
            "idx": int(t.get("index", i)), "speaker": t["speaker_role"], "text": human or machine,
            "machine_text": machine or None, "start_seconds": None if start_ms is None else round(start_ms / 1000, 2),
        })
    started = metadata.get("start_time_ms")
    return {
        "external_id": metadata["sid"],
        "agent_name": (agent.get("metadata") or {}).get("agent_name") or "Unknown",
        "call_type": snake(assigned_type or logged_type) if (assigned_type or logged_type) else None,
        "started_at": datetime.fromtimestamp(started / 1000, timezone.utc) if started else None,
        "logged": logged, "logged_task_type": snake(logged_type) if logged_type else None,
        "assigned": assigned, "turns": turns, "raw_metadata": metadata, "raw_transcript": transcript,
    }


def _norm(ftype: str, value: Any) -> Any:
    s = str(value).strip().lower()
    if ftype == "amount":
        try:
            return float(s.replace("$", "").replace(",", ""))
        except ValueError:
            return s
    if ftype == "phone":
        return re.sub(r"\D", "", s)
    for word in ("your ", "my ", "the ", " account"):
        s = s.replace(word, "")
    return s.strip()


def _band(common: dict, lost: int) -> str:
    if lost <= 0:
        return "none"
    for b in common["severity"]["bands"]:
        if b["min_points_lost"] <= lost and (b["max_points_lost"] is None or lost <= b["max_points_lost"]):
            return b["name"]
    return common["severity"]["bands"][-1]["name"]


def seed_steps(proc: dict, common: dict, call: dict) -> dict:
    """Step results for demo data, WITHOUT a model. Only what the metadata can decide is checked:
    the logged task type, and the logged values against the assigned task (standing in for what the caller asked).
    Steps that need the conversation are marked completed when they have no sub-checks (assumed, not checked) and
    under_review when they have sub-checks that need the model (read-back, stated balance, confirmation).
    """
    fields = {f["key"]: f for f in proc["fields"]}
    steps, totals = [], {"lost": 0, "completed": 0, "missed": 0, "wrong": 0, "under_review": 0}
    for pos, s in enumerate(proc["steps"], 1):
        subs, comparison, lost, review = [], [], 0, 0
        for sc in s["sub_checks"]:
            status = "under_review"
            if sc["type"] == "logged_task_type":
                status = "passed" if call["logged_task_type"] == sc["expected"] else "failed"
            elif sc["type"] == "logged_matches_request" and call["assigned"]:
                ok = True
                for key in sc["fields"]:
                    ftype = fields[key]["type"]
                    asked, logged = call["assigned"].get(key), call["logged"].get(key)
                    match = logged is not None and asked is not None and _norm(ftype, asked) == _norm(ftype, logged)
                    ok &= match
                    comparison.append({"field": key, "caller_asked": asked, "logged": logged, "match": match})
                status = "passed" if ok else "failed"
            subs.append({"key": sc["key"], "description": sc["description"], "points": sc["points"], "status": status})
            lost += sc["points"] if status == "failed" else 0
            review += sc["points"] if status == "under_review" else 0
        if lost:
            status, detail = "wrong", "; ".join(x["description"] for x in subs if x["status"] == "failed") + " (failed)"
        elif review:
            status, detail = "under_review", "Needs the model's read of the conversation (demo seed)."
        else:
            status, detail = "completed", None if s["sub_checks"] else "Demo seed: assumed done, not checked against the transcript."
        steps.append({
            "step_key": s["key"], "position": pos, "name": s["name"], "points": s["points"], "status": status,
            "severity": _band(common, lost), "points_lost": lost, "points_under_review": review, "detail": detail,
            "sub_checks": subs, "comparison": comparison or None,
        })
        totals["lost"] += lost
        totals[status] += 1
    return {"steps": steps, "score": 100 - totals["lost"], "points_lost": totals["lost"], **{k: totals[k] for k in ("completed", "missed", "wrong", "under_review")}}
