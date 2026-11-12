"""PromptTemplateSource: the shared _common.json, read on every request so a missing file answers 503."""

from __future__ import annotations

import json
from pathlib import Path

from app.application.ports import RulesUnavailable


class JsonPromptTemplate:
    def __init__(self, rules_dir: Path) -> None:
        self.rules_dir = Path(rules_dir)

    async def load(self) -> dict:
        try:
            return json.loads((self.rules_dir / "_common.json").read_text())
        except FileNotFoundError as exc:
            raise RulesUnavailable(exc.filename) from exc
