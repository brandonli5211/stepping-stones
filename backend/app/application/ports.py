"""Application ports for use cases."""

from collections.abc import Collection, Mapping, Sequence
from datetime import datetime
from typing import Protocol

from app.domain.call_list import CallRecord, CallWindow, ListFilter, WeekTotals
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


class Clock(Protocol):
    """The reference instant for "now"."""

    def now(self) -> datetime:
        """An aware datetime."""


class CallListReader(Protocol):
    """Reads what the calls list needs."""

    async def recent_calls(self, window: CallWindow, filters: ListFilter, limit: int) -> Sequence[CallRecord]:
        """Calls in the window that pass the filters, newest first, each with its steps in step order."""

    async def count_calls(self, window: CallWindow) -> int:
        """Number of calls in the window."""

    async def week_totals(self, window: CallWindow) -> Sequence[WeekTotals]:
        """Steps completed and total per UTC Monday-start week in the window, oldest week first."""
