from app.load_calls import DEACTIVATE_OTHER_VERSIONS, UPSERT_PROCEDURE, upsert_procedure


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, params))

    def fetchone(self):
        return (7,)


DOC = {"call_type": "transfer_money", "version": 3, "name": "Transfer money", "steps": []}


def test_other_versions_are_deactivated_before_the_insert():
    cur = FakeCursor()

    assert upsert_procedure(cur, DOC) == 7
    assert [sql for sql, _ in cur.executed] == [DEACTIVATE_OTHER_VERSIONS, UPSERT_PROCEDURE]
    assert cur.executed[0][1] == ("transfer_money", 3)


def test_rerunning_a_version_keeps_its_stored_rules():
    on_conflict = UPSERT_PROCEDURE.split("ON CONFLICT", 1)[1]

    assert "is_active = true" in on_conflict
    assert "rules" not in on_conflict
    assert "name" not in on_conflict
