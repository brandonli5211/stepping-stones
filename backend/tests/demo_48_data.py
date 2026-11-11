# The 48 demo calls seeded like `load_calls --demo-results` and scored by ApplyDemoResults, in memory.
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.adapters.files.demo_results_files import read_results_csv, read_severity_bands
from app.application.apply_demo_results import ApplyDemoResults
from app.call_parse import parse_call, seed_steps
from app.domain.demo_results import StoredCall, StoredStep

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "sample" / "demo_48"
RULES = REPO / "docs" / "procedures" / "schema3"
DEMO_TODAY = datetime(2026, 10, 9, 23, 59, 59, tzinfo=timezone.utc)


class MemoryCallStore:
    def __init__(self, calls):
        self.calls = calls
        self.saved = []

    async def find_calls(self, external_ids):
        return {i: self.calls[i] for i in external_ids if i in self.calls}

    async def save_results(self, calls):
        self.saved = list(calls)


def load_demo_48():
    common = json.loads((RULES / "_common.json").read_text(encoding="utf-8"))
    procedures = [json.loads(p.read_text(encoding="utf-8")) for p in RULES.glob("*.json") if not p.name.startswith("_")]
    procedures = {doc["call_type"]: doc for doc in procedures}
    stored = {}
    for meta in sorted((DEMO / "metadata").glob("*.json")):
        call = parse_call(json.loads((DEMO / "transcript" / meta.name).read_text(encoding="utf-8")),
                          json.loads(meta.read_text(encoding="utf-8")))
        steps = seed_steps(procedures[call["call_type"]], common, call)["steps"]
        stored[call["external_id"]] = StoredCall(call["external_id"], call["call_type"], tuple(
            StoredStep(s["step_key"], s["name"], s["points"], s["status"], s["detail"]) for s in steps))
    store = MemoryCallStore(stored)
    outcome = asyncio.run(ApplyDemoResults(store=store, bands=read_severity_bands(RULES)).execute(
        read_results_csv(DEMO / "results.csv")))
    names = {key: doc["name"] for key, doc in procedures.items()}
    return outcome, stored, store.saved, names
