"""FastAPI health route. Delegates to CheckHealth; does not run SQL itself."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.database_probe import SqlAlchemyDatabaseProbe
from app.adapters.persistence.engine import get_session
from app.application.check_health import CheckHealth, HealthStatus

router = APIRouter()


async def get_check_health(
    session: AsyncSession = Depends(get_session),
) -> CheckHealth:
    return CheckHealth(probe=SqlAlchemyDatabaseProbe(session))


@router.get("/api/health")
async def health(check: CheckHealth = Depends(get_check_health)) -> dict[str, str]:
    status: HealthStatus = await check.execute()
    return status.as_dict()
