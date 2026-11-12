import asyncio
import io
import json
import threading
import urllib.error

import pytest

from app.adapters.llm.ollama import OllamaModel, build_request, normalize_host
from app.application.ports import ModelUnavailable


class StandInModel:
    """A fake urlopen standing in for the Ollama server."""

    def __init__(self, reply=None, error=None):
        self.reply = reply if reply is not None else {"response": '{"ok": true}'}
        self.error = error
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout, threading.current_thread()))
        if self.error:
            raise self.error
        return io.BytesIO(json.dumps(self.reply).encode())


def test_normalize_host():
    assert normalize_host("localhost:11434") == "http://localhost:11434"
    assert normalize_host("http://ollama:11434") == "http://ollama:11434"
    assert normalize_host("https://x") == "https://x"


def test_build_request():
    req = build_request("http://h:1/", "m", "the prompt")
    assert req.full_url == "http://h:1/api/generate"
    assert req.get_method() == "POST"
    assert req.get_header("Content-type") == "application/json"
    assert json.loads(req.data) == {"model": "m", "prompt": "the prompt", "stream": False, "format": "json",
                                    "options": {"temperature": 0, "seed": 42}}


def test_ask_uses_default_model_and_timeout():
    stand_in = StandInModel()
    model = OllamaModel("http://h:1", "deepseek-r1:8b", 600.0, urlopen=stand_in)
    assert asyncio.run(model.ask("p", None)) == ("deepseek-r1:8b", '{"ok": true}')
    request, timeout, _ = stand_in.requests[0]
    assert json.loads(request.data)["model"] == "deepseek-r1:8b"
    assert timeout == 600.0


def test_ask_uses_requested_model():
    stand_in = StandInModel()
    name, _ = asyncio.run(OllamaModel("http://h:1", "deepseek-r1:8b", 5, urlopen=stand_in).ask("p", "llama3"))
    assert name == "llama3"
    assert json.loads(stand_in.requests[0][0].data)["model"] == "llama3"


@pytest.mark.parametrize("error,reason", [
    (urllib.error.URLError("refused"), "<urlopen error refused>"),
    (OSError("timed out"), "timed out"),
    (ValueError("bad"), "bad"),
])
def test_transport_errors_become_model_unavailable(error, reason):
    model = OllamaModel("http://h:1", "m", 5, urlopen=StandInModel(error=error))
    with pytest.raises(ModelUnavailable) as caught:
        asyncio.run(model.ask("p", None))
    assert str(caught.value) == f"could not get an answer from Ollama: {reason}"


def test_reply_without_response_key_is_model_unavailable():
    model = OllamaModel("http://h:1", "m", 5, urlopen=StandInModel(reply={"error": "x"}))
    with pytest.raises(ModelUnavailable, match="could not get an answer from Ollama: 'response'"):
        asyncio.run(model.ask("p", None))


def test_ask_runs_the_blocking_call_off_the_event_loop_thread():
    stand_in = StandInModel()

    async def run():
        loop_thread = threading.current_thread()
        await OllamaModel("http://h:1", "m", 5, urlopen=stand_in).ask("p", None)
        return loop_thread

    loop_thread = asyncio.run(run())
    assert stand_in.requests[0][2] is not loop_thread


def test_ask_blocking_returns_response_text_with_timeout():
    stand_in = StandInModel(reply={"response": "hello"})
    model = OllamaModel("http://h:1", "m", 42.0, urlopen=stand_in)
    assert model._ask_blocking("p", "llama3") == "hello"
    request, timeout, _ = stand_in.requests[0]
    assert timeout == 42.0
    assert json.loads(request.data)["model"] == "llama3"


def test_ask_blocking_without_response_key_raises_key_error():
    model = OllamaModel("http://h:1", "m", 5, urlopen=StandInModel(reply={"error": "x"}))
    with pytest.raises(KeyError):
        model._ask_blocking("p", "m")
