"""CheckHealth use case. Depends on ports only."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import DatabaseProbe


@dataclass(frozen=True)
class HealthStatus:
    status: str
    database: str

    def as_dict(self) -> dict[str, str]:
        return {"status": self.status, "database": self.database}


@dataclass(frozen=True)
class CheckHealth:
    """Confirm the API can reach the database through a probe port."""

    probe: DatabaseProbe

    async def execute(self) -> HealthStatus:
        await self.probe.ping()
        return HealthStatus(status="ok", database="connected")
