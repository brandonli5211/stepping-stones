"""API response shapes (Pydantic schemas).

models.py describes what is stored. schemas.py describes what the API sends back.
Keeping them separate means we can change the database without breaking the frontend.
FastAPI uses these to validate output and to build the docs page at /docs.
"""
from pydantic import BaseModel, ConfigDict


class TurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    turn_number: int
    speaker: str
    text: str
    dialog_acts: list[str]


class ConversationSummary(BaseModel):
    """One row in the call list (no transcript, so the list stays small)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    task_type: str


class ConversationDetail(ConversationSummary):
    """A full call: summary fields + what the agent logged + every turn."""

    captured_by_agent: dict
    turns: list[TurnOut]
