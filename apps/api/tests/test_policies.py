from app.domain.policies import evaluate_project


def test_project_policy_accepts_constrained_supported_work() -> None:
    decision = evaluate_project("dashboard", "Build a reporting dashboard", 30)
    assert decision.eligible
    assert not decision.manual_review


def test_project_policy_rejects_prohibited_work_deterministically() -> None:
    decision = evaluate_project("dashboard", "Build a biometric identification dashboard", 20)
    assert not decision.eligible
    assert decision.manual_review
    assert "biometric identification" in decision.reasons[0]


def test_project_policy_routes_restricted_data_to_manual_review() -> None:
    decision = evaluate_project(
        "dashboard",
        "Build a constrained reporting dashboard",
        20,
        data_sensitivity="restricted",
    )

    assert not decision.eligible
    assert decision.manual_review
    assert "sensitive data" in decision.reasons[0]
