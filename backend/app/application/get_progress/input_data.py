"""Input Data for GetProgress."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetProgressInputData:
    agent_id: int | None = None  # None: every agent's calls
