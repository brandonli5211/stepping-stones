import asyncio
from pathlib import Path

import pytest

from app.adapters.files.prompt_template import JsonPromptTemplate
from app.application.ports import RulesUnavailable

_RULES = Path(__file__).resolve().parents[2] / "docs" / "procedures" / "schema3"


def test_loads_a_template_file(tmp_path):
    (tmp_path / "_common.json").write_text('{"prompt_template": "x"}')
    assert asyncio.run(JsonPromptTemplate(tmp_path).load()) == {"prompt_template": "x"}


def test_missing_file_is_rules_unavailable_with_full_path(tmp_path):
    with pytest.raises(RulesUnavailable) as caught:
        asyncio.run(JsonPromptTemplate(tmp_path).load())
    assert str(caught.value) == f"missing rules file: {tmp_path / '_common.json'} (set RULES_DIR)"


def test_invalid_json_still_raises_value_error(tmp_path):
    (tmp_path / "_common.json").write_text("{not json")
    with pytest.raises(ValueError):
        asyncio.run(JsonPromptTemplate(tmp_path).load())


def test_real_rules_folder_loads():
    common = asyncio.run(JsonPromptTemplate(_RULES).load())
    assert "prompt_template" in common and "field_types" in common


def test_file_is_read_on_every_load(tmp_path):
    template = JsonPromptTemplate(tmp_path)
    (tmp_path / "_common.json").write_text('{"v": 1}')
    assert asyncio.run(template.load()) == {"v": 1}
    (tmp_path / "_common.json").unlink()
    with pytest.raises(RulesUnavailable):
        asyncio.run(template.load())
