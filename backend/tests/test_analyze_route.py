import asyncio

import pytest
from fastapi import HTTPException

from app.adapters.http.analyze import AnalyzeRequest, analyze_call
from app.application.ports import ModelUnavailable, RulesUnavailable
from app.domain.call_analysis import CallNotFound, NoTranscript


class FailingUseCase:
    def __init__(self, error):
        self.error = error

    async def execute(self, call_id, model_name=None, dry_run=False):
        raise self.error


@pytest.mark.parametrize("error,status", [
    (CallNotFound(5), 404),
    (NoTranscript(5), 422),
    (RulesUnavailable("/r/_common.json"), 503),
    (ModelUnavailable("refused"), 503),
], ids=["not-found", "no-transcript", "no-rules", "no-model"])
def test_error_status(error, status):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(analyze_call(5, AnalyzeRequest(dry_run=True), use_case=FailingUseCase(error)))

    assert caught.value.status_code == status
    assert caught.value.detail == str(error)
