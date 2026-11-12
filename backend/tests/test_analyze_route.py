import asyncio
import importlib
import inspect
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.adapters.http.analyze as analyze_module
from app.adapters.http.analyze import AnalyzeRequest, analyze_call, get_analyze_call, present_analysis
from app.adapters.persistence.call_analysis_source import SqlAlchemyCallAnalysisSource
from app.application.analyze_call import AnalyzeCall
from app.application.ports import ModelUnavailable, RulesUnavailable
from app.domain.call_analysis import CallNotFound, ModelAnalysis, NoTranscript, PromptPreview

PREVIEW = PromptPreview(5, "abc", "pay_bill", "the prompt")
ANALYSIS = ModelAnalysis(5, "abc", "pay_bill", "deepseek-r1:8b", {"a": 1}, '{"a": 1}')


class FakeUseCase:
    def __init__(self, result=PREVIEW, error=None):
        self.result, self.error, self.calls = result, error, []

    async def execute(self, call_id, model_name=None, dry_run=False):
        self.calls.append((call_id, model_name, dry_run))
        if self.error:
            raise self.error
        return self.result


def test_present_preview_exact_keys():
    body = present_analysis(PREVIEW)
    assert body == {"id": 5, "external_id": "abc", "call_type": "pay_bill", "prompt": "the prompt"}
    assert list(body) == ["id", "external_id", "call_type", "prompt"]


def test_present_analysis_exact_keys():
    body = present_analysis(ANALYSIS)
    assert body == {"id": 5, "external_id": "abc", "call_type": "pay_bill", "model": "deepseek-r1:8b",
                    "result": {"a": 1}, "raw": '{"a": 1}'}
    assert list(body) == ["id", "external_id", "call_type", "model", "result", "raw"]


def test_analyze_request_defaults():
    assert AnalyzeRequest() == AnalyzeRequest(model=None, dry_run=False)


def test_handler_passes_body_and_presents():
    use_case = FakeUseCase(result=ANALYSIS)
    body = asyncio.run(analyze_call(5, AnalyzeRequest(model="llama3", dry_run=False), use_case=use_case))
    assert use_case.calls == [(5, "llama3", False)]
    assert body == present_analysis(ANALYSIS)


def test_handler_missing_body_is_default_request():
    use_case = FakeUseCase()
    asyncio.run(analyze_call(5, None, use_case=use_case))
    assert use_case.calls == [(5, None, False)]


@pytest.mark.parametrize("error,status", [
    (CallNotFound(5), 404),
    (NoTranscript(5), 422),
    (RulesUnavailable("/r/_common.json"), 503),
    (ModelUnavailable("refused"), 503),
])
def test_handler_maps_errors(error, status):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(analyze_call(5, AnalyzeRequest(dry_run=True), use_case=FakeUseCase(error=error)))
    assert caught.value.status_code == status
    assert caught.value.detail == str(error)


def test_handler_holds_no_sql_settings_or_http_client():
    source = inspect.getsource(analyze_module.analyze_call)
    for forbidden in ("select(", "session.", "os.environ", "urlopen", "getenv"):
        assert forbidden not in source
    assert inspect.iscoroutinefunction(analyze_module.analyze_call)


def test_get_analyze_call_wires_source_and_state_adapters():
    template, model = object(), object()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(prompt_template=template, language_model=model)))
    session = object()
    use_case = asyncio.run(get_analyze_call(request, session))
    assert isinstance(use_case, AnalyzeCall)
    assert isinstance(use_case.calls, SqlAlchemyCallAnalysisSource) and use_case.calls._session is session
    assert use_case.template is template and use_case.model is model


def test_main_routes_and_old_module_gone():
    from app.main import app

    routes = [(r.path, sorted(r.methods)) for r in app.routes if hasattr(r, "methods")]
    assert routes.count(("/calls/{call_id}", ["POST"])) == 1
    assert ("/calls", ["GET"]) in routes
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.calls_api")
