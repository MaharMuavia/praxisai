import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.models import Base, InternshipApplication
from app.internships.policies import (
    domain_matches,
    is_application_complete,
    normalize_domain,
    normalize_email,
)
from app.internships.service import ValidationFailure, weighted_score
from app.internships.storage import LocalInternshipStorage


def test_email_normalization_is_case_and_idna_safe() -> None:
    assert normalize_email("Student@XN--EXMPLE-CUA.COM") == "student@exämple.com"
    assert normalize_domain("Sub.Exämple.com.") == "sub.xn--exmple-cua.com"


def test_domain_matching_is_exact_unless_subdomains_are_explicit() -> None:
    assert domain_matches(
        email_domain_value="students.example.edu",
        approved_domain="example.edu",
        allow_subdomains=True,
    )
    assert not domain_matches(
        email_domain_value="students.example.edu",
        approved_domain="example.edu",
        allow_subdomains=False,
    )
    assert not domain_matches(
        email_domain_value="example.edu.attacker.test",
        approved_domain="example.edu",
        allow_subdomains=True,
    )


def test_application_completion_requires_server_owned_fields() -> None:
    incomplete = InternshipApplication(
        applicant_user_id=uuid.uuid4(),
        program_id=uuid.uuid4(),
        cohort_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
    )
    assert not is_application_complete(incomplete)
    incomplete.primary_track_id = uuid.uuid4()
    incomplete.education_status = "Undergraduate"
    incomplete.degree_program = "Computer Science"
    incomplete.country = "PK"
    incomplete.technical_background = "Python"
    incomplete.motivation = "I want to learn through evidence."
    incomplete.weekly_availability_hours = 12
    assert is_application_complete(incomplete)


def test_weighted_review_score_is_deterministic() -> None:
    rubric = [
        {"id": "a", "weight": 60, "max_score": 100},
        {"id": "b", "weight": 40, "max_score": 100},
    ]
    assert (
        weighted_score(
            [{"criterion_id": "a", "score": 80}, {"criterion_id": "b", "score": 90}], rubric
        )
        == 84
    )


def test_weighted_review_score_rejects_unknown_criteria() -> None:
    with pytest.raises(ValidationFailure, match="unknown rubric"):
        weighted_score(
            [{"criterion_id": "unknown", "score": 100}],
            [{"id": "a", "weight": 100, "max_score": 100}],
        )


@pytest.mark.asyncio
async def test_internship_tables_are_metadata_backed() -> None:
    expected = {
        "internship_programs",
        "internship_cohorts",
        "internship_applications",
        "internship_cohort_enrollments",
        "internship_units",
        "internship_student_assignments",
        "internship_submissions",
        "internship_reviews",
        "internship_certificates",
        "university_email_domains",
    }
    assert expected.issubset(Base.metadata.tables)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


def test_local_upload_storage_hashes_bytes_and_blocks_path_traversal(tmp_path) -> None:
    storage = LocalInternshipStorage(tmp_path)
    assert storage.put("student/upload/report.pdf", b"demo") == (
        "2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea"
    )
    assert storage.read("student/upload/report.pdf") == b"demo"
    with pytest.raises(ValueError, match="escapes"):
        storage.put("../outside.txt", b"blocked")


@pytest.mark.asyncio
async def test_local_upload_storage_rejects_streams_over_declared_limit(tmp_path) -> None:
    storage = LocalInternshipStorage(tmp_path)

    async def chunks() -> AsyncIterator[bytes]:
        yield b"1234"
        yield b"56"

    with pytest.raises(ValueError, match="byte limit"):
        await storage.put_stream("oversized.bin", chunks(), max_bytes=5)
    assert not (tmp_path / "oversized.bin").exists()
