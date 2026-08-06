from datetime import UTC, datetime, timedelta

import pytest

from app.auth.capabilities import role_has_capability
from app.internships.assignments.policies import evaluate_assignment_unlock
from app.internships.reviews.scoring import RubricValidationError, weighted_score
from app.internships.submissions.service import canonical_evidence_hash
from app.internships.uploads.scanning import DemoScanner, DisabledProductionScanner


def test_internship_capability_matrix_keeps_staff_boundaries() -> None:
    assert role_has_capability("reviewer", "internships:reviews:view_assigned")
    assert role_has_capability("reviewer", "internships:reviews:finalize")
    assert not role_has_capability("reviewer", "internships:applications:decide")
    assert not role_has_capability("reviewer", "internships:certificates:issue")
    assert role_has_capability("technical_lead", "internships:reviews:view_assigned")
    assert not role_has_capability("technical_lead", "internships:cohorts:manage")
    assert role_has_capability("coordinator", "internships:completion:decide")
    assert not role_has_capability("student", "internships:analytics:view")


def test_weighted_score_requires_the_exact_rubric() -> None:
    rubric = [
        {"id": "quality", "max_score": 10, "weight": 60},
        {"id": "evidence", "max_score": 10, "weight": 40},
    ]
    assert (
        weighted_score(
            [
                {"criterion_id": "quality", "score": 8},
                {"criterion_id": "evidence", "score": 10},
            ],
            rubric,
        )
        == 88
    )
    with pytest.raises(RubricValidationError, match="duplicate"):
        weighted_score(
            [
                {"criterion_id": "quality", "score": 8},
                {"criterion_id": "quality", "score": 8},
            ],
            rubric,
        )
    with pytest.raises(RubricValidationError, match="missing"):
        weighted_score([{"criterion_id": "quality", "score": 8}], rubric)


def test_assignment_unlock_reports_authoritative_missing_requirements() -> None:
    now = datetime.now(UTC)
    result = evaluate_assignment_unlock(
        now=now,
        release_at=now - timedelta(minutes=1),
        enrollment_active=True,
        previous_week_complete=False,
        required_units_complete=True,
        quiz_passed=False,
        prior_assignment_passed=True,
        human_released=True,
    )
    assert result.state == "LOCKED"
    assert result.missing_requirements == ("previous week complete", "quiz threshold")


def test_production_scanner_never_reports_clean() -> None:
    result = DisabledProductionScanner().scan(
        b"%PDF-1.7", declared_content_type="application/pdf", filename="report.pdf"
    )
    assert result.state == "QUARANTINED"
    assert result.state != "CLEAN"


def test_demo_scanner_rejects_magic_byte_mismatch_and_malware_fixture() -> None:
    scanner = DemoScanner()
    mismatch = scanner.scan(
        b"not a pdf", declared_content_type="application/pdf", filename="report.pdf"
    )
    assert mismatch.state == "REJECTED"
    malware = scanner.scan(
        b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
        declared_content_type="text/plain",
        filename="notes.txt",
    )
    assert malware.state == "REJECTED"


def test_canonical_hash_binds_evidence_metadata() -> None:
    base = {
        "assignment_id": "assignment-1",
        "artifact_snapshot": [{"upload_id": "u1", "sha256": "a" * 64, "size_bytes": 10}],
        "text_fields": {"summary": "Evidence"},
    }
    changed = {**base, "artifact_snapshot": [{**base["artifact_snapshot"][0], "size_bytes": 11}]}
    assert canonical_evidence_hash(base) != canonical_evidence_hash(changed)
