"""Application ports for use cases."""

from collections.abc import Collection, Mapping, Sequence
from typing import Protocol

from app.domain.demo_results import ScoredCall, StoredCall


class DatabaseProbe(Protocol):
    """Reports whether the application database accepts a connection."""

    async def ping(self) -> None:
        """Raise if the database cannot be reached."""


class DemoCallStore(Protocol):
    """Loads stored calls and saves their rescored results.

    save_results writes inside the caller's unit of work; the caller commits or rolls back.
    """

    async def find_calls(self, external_ids: Collection[str]) -> Mapping[str, StoredCall]:
        """Stored calls keyed by external id. Ids with no call are absent."""

    async def save_results(self, calls: Sequence[ScoredCall]) -> None:
        """Write the new step results and call totals."""
