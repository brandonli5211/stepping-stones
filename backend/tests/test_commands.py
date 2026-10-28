import sys

from app.commands import migrate, serve, test as run_tests


def test_test_command_launches_pytest():
    launched = {}

    def runner(command):
        launched["command"] = tuple(command)
        return 0

    assert run_tests(run=runner) == 0
    command = launched["command"]
    assert command[:3] == (sys.executable, "-m", "pytest")
    assert command[3].endswith("/tests") or command[3] == "tests"
    assert "uvicorn" not in command
    assert "alembic" not in command
    assert not any("docker" in part or "compose" in part for part in command)


def test_serve_launches_uvicorn_not_alembic():
    launched = {}

    def runner(command):
        launched["command"] = tuple(command)
        return 0

    assert serve(run=runner) == 0
    command = launched["command"]
    assert "uvicorn" in command
    assert "app.main:app" in command
    assert "0.0.0.0" in command
    assert "8000" in command
    assert "--reload" in command
    assert "alembic" not in command


def test_migrate_upgrades_head_without_serving_or_dropping():
    launched = {}

    def runner(command):
        launched["command"] = tuple(command)
        return 0

    assert migrate(run=runner) == 0
    command = launched["command"]
    assert command[-3:] == ("alembic", "upgrade", "head")
    assert "uvicorn" not in command
    assert "downgrade" not in command
    assert "drop" not in " ".join(command).lower()
