"""Create the tables and load sample calls into Postgres.

Run from the backend/ folder:
    python -m scripts.seed                          # loads ../data/sample_calls.json
    python -m scripts.seed path/to/other_calls.json

Safe to run more than once: each call is deleted and re-inserted.
"""
import json
import sys
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import Conversation, Turn

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "data" / "sample_calls.json"


def call_to_conversation(call: dict) -> Conversation:
    """Turn one curated HVB call (a dict from JSON) into a Conversation row with its Turns."""
    tasks = call.get("source_fields", {}).get("task_assigned") or ["unknown"]
    conversation = Conversation(
        id=call["id"],
        agent_id=call["agent_id"],
        task_type=tasks[0],
        captured_by_agent=call.get("customer_record", {}).get("captured_by_agent", {}),
    )
    conversation.turns = [
        Turn(
            turn_number=turn["n"],
            speaker=turn["speaker"],
            text=turn["text"],
            dialog_acts=turn.get("dialog_acts", []),
        )
        for turn in call["turns"]
    ]
    return conversation


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    calls = json.loads(path.read_text(encoding="utf-8"))

    # Creates any tables in models.py that don't exist yet. (Doesn't alter existing tables —
    # if you change a model, see "Changing the database" in docs/SETUP.md.)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        for call in calls:
            existing = db.get(Conversation, call["id"])
            if existing:
                db.delete(existing)
                db.flush()
            db.add(call_to_conversation(call))
        db.commit()

    print(f"Loaded {len(calls)} calls from {path}")


if __name__ == "__main__":
    main()
