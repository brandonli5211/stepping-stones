"""Application ports for use cases."""

from typing import Protocol

from app.domain.call_detail import CallRecord


class DatabaseProbe(Protocol):
    """Reports whether the application database accepts a connection."""

    async def ping(self) -> None:
        """Raise if the database cannot be reached."""


class CallDetailReader(Protocol):
    """Reads one stored call with its turns and step results. Read only."""

    async def get(self, call_id: int) -> CallRecord | None:
        """The call with this id, or None when no call has it."""
