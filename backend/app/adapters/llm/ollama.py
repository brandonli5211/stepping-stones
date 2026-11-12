"""LanguageModel backed by a local Ollama server, using only the standard library.

The blocking HTTP call runs in a worker thread so the event loop stays free.
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from collections.abc import Callable

from app.application.ports import ModelUnavailable


def normalize_host(host: str) -> str:
    return host if "://" in host else "http://" + host


def build_request(host: str, name: str, prompt: str) -> urllib.request.Request:
    payload = {"model": name, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0, "seed": 42}}
    return urllib.request.Request(host.rstrip("/") + "/api/generate", json.dumps(payload).encode(),
                                  {"Content-Type": "application/json"})


class OllamaModel:
    def __init__(self, host: str, default_model: str, timeout: float,
                 urlopen: Callable = urllib.request.urlopen) -> None:
        self.host, self.default_model, self.timeout = host, default_model, timeout
        self._urlopen = urlopen

    def _ask_blocking(self, prompt: str, name: str) -> str:
        with self._urlopen(build_request(self.host, name, prompt), timeout=self.timeout) as resp:
            return json.load(resp)["response"]

    async def ask(self, prompt: str, model: str | None) -> tuple[str, str]:
        name = model or self.default_model
        try:
            answer = await asyncio.to_thread(self._ask_blocking, prompt, name)
        except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
            raise ModelUnavailable(str(exc)) from exc
        return name, answer
