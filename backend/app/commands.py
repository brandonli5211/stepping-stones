import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

ProcessRunner = Callable[[Sequence[str]], int]

_BACKEND = Path(__file__).resolve().parent.parent
_TESTS = _BACKEND / "tests"


def _default_runner(command: Sequence[str]) -> int:
    completed = subprocess.run(list(command), check=False, cwd=_BACKEND)
    return completed.returncode


def test(run: ProcessRunner | None = None) -> int:
    """Run the backend test suite. Returns pytest's exit code."""
    runner = _default_runner if run is None else run
    return runner((sys.executable, "-m", "pytest", str(_TESTS)))


def serve(run: ProcessRunner | None = None) -> int:
    """Start the API on port 8000. Does not run Alembic."""
    command = (
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    )
    if run is None:
        os.execv(command[0], list(command))
    return run(command)


def migrate(run: ProcessRunner | None = None) -> int:
    """Apply schema history through head. Does not start the API."""
    runner = _default_runner if run is None else run
    return runner((sys.executable, "-m", "alembic", "upgrade", "head"))
