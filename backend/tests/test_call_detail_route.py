import asyncio
import inspect
import json
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

import app.adapters.http.call_detail as module
from app.adapters.http.call_detail import _step, _type_details, get_call_detail, get_get_call_detail, present
from app.adapters.http.call_detail_schema import CallDetailOut, EmptyDetailsOut, TransferMoneyDetailsOut
from app.application.get_call_detail import GetCallDetail
from app.domain.call_detail import (
    CallNotFound,
    EmptyDetails,
    StepDetail,
    StepRecord,
    TransferMoneyDetails,
    build_call_detail,
)
from call_detail_fixtures import check_balance_call, transfer_money_call

_CONTRACT = Path(__file__).resolve().parents[2] / "docs" / "api-contract.md"


def _contract_examples() -> list[str]:
    return re.findall(r"```json\n(.*?)```", _CONTRACT.read_text(encoding="utf-8"), re.S)


class _FakeUseCase:
    def __init__(self, detail=None, error=None):
        self.detail, self.error, self.asked = detail, error, []

    async def execute(self, call_id):
        self.asked.append(call_id)
        if self.error:
            raise self.error
        return self.detail


@pytest.mark.skipif(
    not _CONTRACT.is_file(),
    reason="docs/api-contract.md is outside backend/; run from the repo or with docs mounted (docker compose)",
)
def test_present_matches_the_published_transfer_money_example():
    body = present(build_call_detail(transfer_money_call())).model_dump(mode="json")
    assert body == json.loads(_contract_examples()[0])


def test_present_gives_an_empty_block_for_another_call_type():
    out = present(build_call_detail(check_balance_call()))
    assert out.type_details == EmptyDetailsOut(type="check_balance")
    assert out.flags == []
    assert out.score.score == 100


def test_present_marks_the_transfer_money_block():
    assert isinstance(present(build_call_detail(transfer_money_call())).type_details, TransferMoneyDetailsOut)


def test_schema_rejects_a_response_that_does_not_fit():
    body = present(build_call_detail(transfer_money_call())).model_dump(mode="json")
    body["score"]["score"] = "forty five"
    with pytest.raises(ValueError):
        CallDetailOut.model_validate(body)


def test_schema_rejects_a_flag_with_an_unknown_severity():
    body = present(build_call_detail(transfer_money_call())).model_dump(mode="json")
    body["flags"][0]["severity"] = "huge"
    with pytest.raises(ValueError):
        CallDetailOut.model_validate(body)


def test_schema_rejects_a_transfer_money_block_without_its_table():
    body = present(build_call_detail(transfer_money_call())).model_dump(mode="json")
    body["type_details"] = {"type": "transfer_money"}
    with pytest.raises(ValueError):
        CallDetailOut.model_validate(body)
    with pytest.raises(ValueError, match="has its own type_details block"):
        EmptyDetailsOut(type="transfer_money")


def test_not_a_type_with_details_validator_checks_the_type():
    assert EmptyDetailsOut._not_a_type_with_details("pay_bill") == "pay_bill"
    with pytest.raises(ValueError, match="has its own type_details block"):
        EmptyDetailsOut._not_a_type_with_details("transfer_money")


def test_schema_reads_an_unknown_type_as_an_empty_block():
    body = present(build_call_detail(check_balance_call())).model_dump(mode="json")
    body["type_details"] = {"type": "some_new_type"}
    assert CallDetailOut.model_validate(body).type_details == EmptyDetailsOut(type="some_new_type")


def test_route_returns_the_presented_detail():
    use_case = _FakeUseCase(detail=build_call_detail(transfer_money_call()))
    out = asyncio.run(get_call_detail(6, use_case=use_case))
    assert out.score.score == 45
    assert use_case.asked == [6]


def test_route_turns_not_found_into_404():
    use_case = _FakeUseCase(error=CallNotFound(999999))
    with pytest.raises(HTTPException) as error:
        asyncio.run(get_call_detail(999999, use_case=use_case))
    assert error.value.status_code == 404
    assert error.value.detail == "no call with id 999999"


def test_route_dependency_builds_the_use_case_on_the_session():
    use_case = asyncio.run(get_get_call_detail(session=object()))
    assert isinstance(use_case, GetCallDetail)


def test_route_handler_is_async():
    assert inspect.iscoroutinefunction(module.get_call_detail)


def test_step_maps_a_step_without_evidence():
    out = _step(StepDetail(StepRecord("m", 1, "M", 10, "missed", points_lost=10, description="Do M."), None))
    assert out.details.evidence is None
    assert (out.points_lost, out.details.description) == (10, "Do M.")


def test_step_takes_coaching_from_the_domain_not_the_stored_step():
    stored = StepRecord("c", 1, "C", 10, "completed", coaching="Stray tip.")
    assert _step(StepDetail(stored, None, None)).details.coaching is None
    assert _step(StepDetail(stored, None, "Next time ...")).details.coaching == "Next time ..."


def test_type_details_maps_each_block_type():
    assert _type_details(EmptyDetails("pay_bill")) == EmptyDetailsOut(type="pay_bill")
    assert _type_details(TransferMoneyDetails(())) == TransferMoneyDetailsOut(type="transfer_money", fields=[])


def test_present_carries_the_option_a_values():
    out = present(build_call_detail(transfer_money_call()))
    assert out.steps[4].details.description.startswith("Log the transfer correctly")
    assert [r.result for r in out.type_details.fields] == ["match", "reversed", "reversed"]
    assert out.flags[0].message == "Moved $114 savings → checking. The caller asked for checking → savings."


def test_path_parameter_is_an_integer_so_external_ids_are_refused():
    from app.main import app

    params = app.openapi()["paths"]["/calls/{call_id}"]["get"]["parameters"]
    assert params[0]["name"] == "call_id" and params[0]["schema"]["type"] == "integer"


def test_endpoint_is_in_the_catalogue_with_its_schema():
    from app.main import app

    operation = app.openapi()["paths"]["/calls/{call_id}"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("CallDetailOut")
    assert "404" in operation["responses"]
