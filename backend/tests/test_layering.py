import ast
from pathlib import Path

import pytest

import app.application
import app.domain

FORBIDDEN = {"fastapi", "sqlalchemy", "alembic", "psycopg"}
MODULES = [
    (package.__name__, path)
    for package in (app.domain, app.application)
    for path in sorted(Path(package.__file__).parent.rglob("*.py"))
]


@pytest.mark.parametrize("package,path", MODULES, ids=[f"{p.split('.')[-1]}.{f.stem}" for p, f in MODULES])
def test_no_framework_imports(package, path):
    imported = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert not {name.split(".")[0] for name in imported} & FORBIDDEN
    assert not [name for name in imported if name.startswith(("app.adapters", "app.infrastructure"))]
    if package == "app.domain":
        assert not [name for name in imported if name.startswith("app.application")]
