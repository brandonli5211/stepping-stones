"""Application ports for use cases."""

from typing import Protocol


class DatabaseProbe(Protocol):
    """Reports whether the application database accepts a connection."""

    async def ping(self) -> None:
        """Raise if the database cannot be reached."""
