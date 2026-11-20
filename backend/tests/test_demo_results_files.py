import json
from pathlib import Path

from app.adapters.files.demo_results_files import read_results_csv
from app.domain.demo_results import evidence_problems, has_evidence

DEMO = Path(__file__).resolve().parents[2] / "sample" / "demo_48"


def test_demo_48_evidence():
    (cited,) = [r for r in read_results_csv(DEMO / "results.csv") if has_evidence(r)]
    transcript = json.loads((DEMO / "transcript" / "a2f086d27b3a4f96.json").read_text(encoding="utf-8"))
    turns = {t["index"]: (t.get("human_transcript") or "").strip() or (t.get("transcript") or "").strip()
             for t in transcript}
    turn_9 = next(t for t in transcript if t["index"] == 9)

    assert (cited.demo_id, cited.external_id) == ("HVB-DEMO-06", "a2f086d27b3a4f96")
    assert (cited.evidence_step, cited.evidence_turn) == ("submit_and_confirm_transfer", "9")
    assert cited.evidence_quote == "okay and that was from your savings to your checking account"
    assert evidence_problems(cited, turns) == []
    assert turn_9["speaker_role"] == "agent"
    assert int(turn_9["start_ms"] / 1000) == 33
