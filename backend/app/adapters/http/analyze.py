"""POST /calls/{call_id}: build the coaching prompt for one stored call and either return it (dry_run) or send it
to the local model. Translates the request, delegates to AnalyzeCall, and maps its errors to HTTP status codes.

Settings (RULES_DIR, OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT) are read once in app.main.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.call_analysis_source import SqlAlchemyCallAnalysisSource
from app.adapters.persistence.engine import get_session
from app.application.analyze_call import AnalyzeCall
from app.application.ports import ModelUnavailable, RulesUnavailable
from app.domain.call_analysis import CallNotFound, ModelAnalysis, NoTranscript, PromptPreview

router = APIRouter()


class AnalyzeRequest(BaseModel):
    model: str | None = None  # Ollama model name; default OLLAMA_MODEL
    dry_run: bool = False  # True: return the prompt without calling the model


def present_analysis(result: PromptPreview | ModelAnalysis) -> dict:
    if isinstance(result, PromptPreview):
        return {"id": result.id, "external_id": result.external_id, "call_type": result.call_type, "prompt": result.prompt}
    return {"id": result.id, "external_id": result.external_id, "call_type": result.call_type, "model": result.model,
            "result": result.result, "raw": result.raw}


async def get_analyze_call(request: Request, session: AsyncSession = Depends(get_session)) -> AnalyzeCall:
    return AnalyzeCall(calls=SqlAlchemyCallAnalysisSource(session), template=request.app.state.prompt_template,
                       model=request.app.state.language_model)


@router.post("/calls/{call_id}")
async def analyze_call(call_id: int, body: AnalyzeRequest | None = None,
                       use_case: AnalyzeCall = Depends(get_analyze_call)) -> dict:
    """call_id is our own call id: the `id` that GET /calls returns."""
    body = body or AnalyzeRequest()
    try:
        result = await use_case.execute(call_id, model_name=body.model, dry_run=body.dry_run)
    except CallNotFound as exc:
        raise HTTPException(404, str(exc))
    except NoTranscript as exc:
        raise HTTPException(422, str(exc))
    except (RulesUnavailable, ModelUnavailable) as exc:
        raise HTTPException(503, str(exc))
    return present_analysis(result)
