import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.adapters.files.shared_steps import JsonSharedSteps
from app.adapters.http.progress.router import get_progress_parts, progress
from app.infrastructure.clock import SystemClock


def test_progress_503_without_rules(tmp_path):
    state = SimpleNamespace(clock=SystemClock(), shared_steps=JsonSharedSteps(tmp_path / "nowhere"))
    parts = asyncio.run(get_progress_parts(SimpleNamespace(app=SimpleNamespace(state=state)), session=object()))

    with pytest.raises(HTTPException) as caught:
        asyncio.run(progress(agent_id=None, parts=parts))

    assert caught.value.status_code == 503
    assert caught.value.detail == f"missing rules file: {tmp_path / 'nowhere' / '_common.json'} (set RULES_DIR)"
