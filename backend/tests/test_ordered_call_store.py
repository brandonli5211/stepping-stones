from app.adapters.persistence.ordered_call_store import required_steps, severity


def test_required_steps_copies_only_domain_safe_rule_fields():
    steps = required_steps({"steps": [{"key": "greet", "points": 5, "name": "Greet", "done_when": "Say hello"}]})
    assert steps[0].key == "greet" and steps[0].name == "Greet" and steps[0].done_when == "Say hello"


def test_severity_is_derived_from_lost_points_not_full_step_value():
    assert [severity(value) for value in (0, 1, 5, 6, 10, 11, 20, 21)] == [
        "none", "slip", "slip", "inaccuracy", "inaccuracy", "mistake", "mistake", "critical"
    ]


def test_required_steps_preserves_sub_checks_for_python_judgment():
    steps = required_steps({"steps": [{
        "key": "submit", "points": 55, "sub_checks": [{
            "key": "read_back", "type": "read_back_matches_request", "points": 5, "fields": ["amount"],
        }],
    }]})
    assert steps[0].kind == "confirmation"
    assert steps[0].checks[0].fields == ("amount",)
