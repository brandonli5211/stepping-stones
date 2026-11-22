"""GET /progress: wire the GetProgress use case for one request, run its controller, return the view model.
No SQL and no rules here."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.http.progress.controller import GetProgressController
from app.adapters.http.progress.presenter import GetProgressPresenter
from app.adapters.http.progress.view_model import ProgressViewModel
from app.adapters.persistence.engine import get_session
from app.adapters.persistence.progress_data_access import SqlAlchemyProgressDataAccess
from app.application.get_progress.interactor import GetProgressInteractor

router = APIRouter()


async def get_progress_parts(
    request: Request, session: AsyncSession = Depends(get_session)
) -> tuple[GetProgressController, ProgressViewModel]:
    """The controller for this request and the view model its presenter fills."""
    view_model = ProgressViewModel()
    interactor = GetProgressInteractor(
        data=SqlAlchemyProgressDataAccess(session),
        shared_steps=request.app.state.shared_steps,
        clock=request.app.state.clock,
        presenter=GetProgressPresenter(view_model),
    )
    return GetProgressController(interactor), view_model


@router.get("/progress")
async def progress(
    agent_id: int | None = None,
    parts: tuple[GetProgressController, ProgressViewModel] = Depends(get_progress_parts),
) -> dict:
    """Progress over the 8 weeks that end this week: weekly percents, this week against the first week,
    the percent per call type, and the steps skipped most.

    agent_id limits everything to that agent's calls. Left out, every agent's calls are counted.
    """
    controller, view_model = parts
    await controller.execute(agent_id)
    if view_model.error is not None:
        raise HTTPException(503, view_model.error)
    return view_model.body()
