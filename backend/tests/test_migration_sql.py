import re
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]


def test_offline_upgrade_creates_app_meta(monkeypatch, capsys):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://tester:secret@db.example:5432/stones",
    )
    monkeypatch.chdir(_BACKEND)

    from alembic import command
    from alembic.config import Config

    config = Config(str(_BACKEND / "alembic.ini"))
    command.upgrade(config, "head", sql=True)
    sql = capsys.readouterr().out

    assert "CREATE TABLE app_meta" in sql
    assert "DROP" not in sql.upper()
    assert re.search(r"\bid\b", sql)
    assert re.search(r"\bkey\b", sql)
    assert re.search(r"\bvalue\b", sql)
