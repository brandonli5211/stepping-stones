import pytest

from app.domain.app_meta import AppMeta, AppMetaValidationError, create_app_meta


def test_create_app_meta_exposes_key_and_value():
    entity = create_app_meta(key="schema", value="starting")
    assert entity.key == "schema"
    assert entity.value == "starting"
    assert entity.id is None


def test_app_meta_rejects_missing_or_empty_key():
    with pytest.raises(AppMetaValidationError):
        AppMeta(key="", value="present")
    with pytest.raises(AppMetaValidationError):
        AppMeta(key="   ", value="present")


def test_app_meta_rejects_missing_or_empty_value():
    with pytest.raises(AppMetaValidationError):
        AppMeta(key="present", value="")
    with pytest.raises(AppMetaValidationError):
        create_app_meta(key="present", value="   ")


def test_domain_module_does_not_import_frameworks():
    import ast

    import app.domain.app_meta as module

    forbidden = {"fastapi", "sqlalchemy", "alembic"}
    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(forbidden)
