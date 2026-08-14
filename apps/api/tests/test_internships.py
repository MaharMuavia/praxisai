import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.auth.service import SessionPrincipal
from app.config import Settings
from app.domain.models import (
    Base,
    InternshipApplication,
    InternshipCohort,
    InternshipProgram,
    InternshipStudentAssignment,
    InternshipUpload,
)
from app.internships import service as internship_service
from app.internships.limits import MAX_CONFIGURABLE_UPLOAD_BYTES
from app.internships.policies import (
    domain_matches,
    is_application_complete,
    normalize_domain,
    normalize_email,
)
from app.internships.schemas import UploadCompleteRequest, UploadInitiateRequest
from app.internships.service import (
    InvalidState,
    ValidationFailure,
    _has_nonblank_artifact_value,
    _upload_finalization_expiry,
    _upload_limits,
    application_window_is_open,
    complete_upload,
    receive_upload_content,
    weighted_score,
)
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


def test_application_window_enforces_status_and_deadline() -> None:
    now = datetime(2026, 8, 11, 12, tzinfo=UTC)
    program = InternshipProgram(
        slug="applications-test",
        name="Applications test",
        public_description="Test program",
        duration_weeks=4,
        status="APPLICATIONS_OPEN",
    )
    cohort = InternshipCohort(
        program_id=uuid.uuid4(),
        name="August cohort",
        slug="august-cohort",
        starts_at=now + timedelta(days=7),
        ends_at=now + timedelta(days=35),
        application_deadline=now + timedelta(days=1),
        capacity=10,
        status="APPLICATIONS_OPEN",
    )

    assert application_window_is_open(program, cohort, at=now)
    cohort.application_deadline = now - timedelta(microseconds=1)
    assert not application_window_is_open(program, cohort, at=now)
    cohort.application_deadline = now + timedelta(days=1)
    program.status = "CLOSED"
    assert not application_window_is_open(program, cohort, at=now)


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


def test_upload_limits_respect_the_hosted_request_ceiling() -> None:
    settings = Settings(_env_file=None, internship_max_upload_bytes=30 * 1024 * 1024)

    maximum, extensions = _upload_limits(settings, "zip", "submission.zip")

    assert maximum == 30 * 1024 * 1024
    assert extensions == {"zip"}


def test_upload_initiation_schema_preserves_configurable_local_limits() -> None:
    local_limit = 100 * 1024 * 1024
    request = UploadInitiateRequest(
        assignment_id=uuid.uuid4(),
        artifact_type="zip",
        filename="submission.zip",
        content_type="application/zip",
        size_bytes=local_limit,
    )
    settings = Settings(_env_file=None, internship_max_upload_bytes=local_limit)

    maximum, _ = _upload_limits(settings, request.artifact_type, request.filename)
    size_schema = UploadInitiateRequest.model_json_schema()["properties"]["size_bytes"]

    assert maximum == local_limit
    assert request.size_bytes == local_limit
    assert size_schema["maximum"] == MAX_CONFIGURABLE_UPLOAD_BYTES
    assert "lower limit" in size_schema["description"]


def test_upload_finalization_expiry_uses_assignment_due_date_with_a_24_hour_minimum() -> None:
    received_at = datetime(2026, 8, 12, 12, tzinfo=UTC)

    assert _upload_finalization_expiry(
        received_at=received_at,
        assignment_due_at=None,
    ) == received_at + timedelta(hours=24)

    assignment_due_at = received_at + timedelta(days=3)
    assert _upload_finalization_expiry(
        received_at=received_at,
        assignment_due_at=assignment_due_at,
    ) == assignment_due_at + timedelta(hours=24)


def test_required_text_artifact_must_contain_nonblank_content() -> None:
    values = {
        "missing": "",
        "whitespace": "  \n\t ",
        "reflection": "What I learned",
    }

    assert not _has_nonblank_artifact_value(values, "missing")
    assert not _has_nonblank_artifact_value(values, "whitespace")
    assert not _has_nonblank_artifact_value(values, "unknown")
    assert _has_nonblank_artifact_value(values, "reflection")


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


@pytest.mark.asyncio
async def test_received_upload_extends_finalization_through_assignment_due_date(
    tmp_path: Path,
) -> None:
    owner_id = uuid.uuid4()
    assignment_due_at = datetime.now(UTC) + timedelta(days=3)
    assignment = InternshipStudentAssignment(
        id=uuid.uuid4(),
        cohort_assignment_id=uuid.uuid4(),
        student_user_id=owner_id,
        state="IN_PROGRESS",
        due_at=assignment_due_at,
    )
    upload = InternshipUpload(
        upload_id="upload-finalization-window",
        owner_user_id=owner_id,
        student_assignment_id=assignment.id,
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=4,
        storage_key="internships/student/finalization/report.pdf",
        state="INITIATED",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    initial_expiry = upload.expires_at
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = upload
    session.get.return_value = assignment

    view = await receive_upload_content(
        session,
        principal=SessionPrincipal(owner_id, uuid.uuid4(), "student"),
        upload_id=upload.upload_id,
        content=b"data",
        settings=Settings(_env_file=None, internship_local_storage_path=tmp_path),
    )

    assert upload.state == "UPLOADED"
    assert upload.expires_at == assignment_due_at + timedelta(hours=24)
    assert upload.expires_at > initial_expiry
    assert view.expires_at == upload.expires_at
    assert view.scan_message is None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("declared_size", "declared_hash"),
    [(5, None), (4, "0" * 64)],
)
async def test_rejected_upload_metadata_mismatch_removes_stored_object(
    tmp_path: Path,
    declared_size: int,
    declared_hash: str | None,
) -> None:
    owner_id = uuid.uuid4()
    storage_key = "internships/student/upload/report.pdf"
    upload = InternshipUpload(
        upload_id="upload-mismatch",
        owner_user_id=owner_id,
        student_assignment_id=uuid.uuid4(),
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=declared_size,
        sha256=declared_hash,
        storage_key=storage_key,
        state="INITIATED",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = upload
    settings = Settings(_env_file=None, internship_local_storage_path=tmp_path)

    with pytest.raises(
        ValidationFailure, match="Uploaded size or SHA-256 does not match initiation metadata"
    ):
        await receive_upload_content(
            session,
            principal=SessionPrincipal(owner_id, uuid.uuid4(), "student"),
            upload_id=upload.upload_id,
            content=b"data",
            settings=settings,
        )

    assert upload.state == "REJECTED"
    assert not (tmp_path / storage_key).exists()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_rejected_upload_cleanup_failure_is_retried_by_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner_id = uuid.uuid4()
    upload = InternshipUpload(
        upload_id="upload-cleanup-retry",
        owner_user_id=owner_id,
        student_assignment_id=uuid.uuid4(),
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=5,
        storage_key="internships/student/cleanup/report.pdf",
        state="INITIATED",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = upload
    cleanup = AsyncMock(return_value=False)
    monkeypatch.setattr(internship_service, "_delete_rejected_upload_object", cleanup)

    with pytest.raises(
        ValidationFailure, match="Uploaded size or SHA-256 does not match initiation metadata"
    ):
        await receive_upload_content(
            session,
            principal=SessionPrincipal(owner_id, uuid.uuid4(), "student"),
            upload_id=upload.upload_id,
            content=b"data",
            settings=Settings(_env_file=None, internship_local_storage_path=tmp_path),
        )

    assert upload.state == "REJECTED_CLEANUP_PENDING"
    assert upload.scan_message == "Upload was rejected; private object cleanup is pending"


@pytest.mark.asyncio
async def test_completion_hash_mismatch_removes_stored_object(tmp_path: Path) -> None:
    owner_id = uuid.uuid4()
    storage_key = "internships/student/upload/report.pdf"
    storage = LocalInternshipStorage(tmp_path)
    stored_hash = storage.put(storage_key, b"data")
    upload = InternshipUpload(
        upload_id="upload-completion-mismatch",
        owner_user_id=owner_id,
        student_assignment_id=uuid.uuid4(),
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=4,
        sha256=stored_hash,
        storage_key=storage_key,
        state="UPLOADED",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = upload
    settings = Settings(_env_file=None, internship_local_storage_path=tmp_path).model_copy(
        update={"app_env": "production"}
    )

    with pytest.raises(ValidationFailure, match="Upload hash does not match"):
        await complete_upload(
            session,
            principal=SessionPrincipal(owner_id, uuid.uuid4(), "student"),
            upload_id=upload.upload_id,
            body=UploadCompleteRequest(sha256="0" * 64),
            settings=settings,
        )

    assert upload.state == "REJECTED"
    assert not (tmp_path / storage_key).exists()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_replayed_content_request_preserves_completed_upload_state(tmp_path: Path) -> None:
    owner_id = uuid.uuid4()
    upload = InternshipUpload(
        upload_id="upload-replay",
        owner_user_id=owner_id,
        student_assignment_id=uuid.uuid4(),
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=4,
        storage_key="internships/student/replay/report.pdf",
        state="CLEAN",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = upload

    with pytest.raises(InvalidState, match="already received"):
        await receive_upload_content(
            session,
            principal=SessionPrincipal(owner_id, uuid.uuid4(), "student"),
            upload_id=upload.upload_id,
            content=b"data",
            settings=Settings(_env_file=None, internship_local_storage_path=tmp_path),
        )

    assert upload.state == "CLEAN"
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_expired_uploaded_object_is_deleted_before_state_transition(tmp_path: Path) -> None:
    owner_id = uuid.uuid4()
    storage_key = "internships/student/expired/report.pdf"
    storage = LocalInternshipStorage(tmp_path)
    stored_hash = storage.put(storage_key, b"data")
    upload = InternshipUpload(
        upload_id="upload-expired-completion",
        owner_user_id=owner_id,
        student_assignment_id=uuid.uuid4(),
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=4,
        sha256=stored_hash,
        storage_key=storage_key,
        state="UPLOADED",
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = upload

    with pytest.raises(InvalidState, match="Upload is expired"):
        await complete_upload(
            session,
            principal=SessionPrincipal(owner_id, uuid.uuid4(), "student"),
            upload_id=upload.upload_id,
            body=UploadCompleteRequest(sha256=stored_hash),
            settings=Settings(_env_file=None, internship_local_storage_path=tmp_path),
        )

    assert upload.state == "EXPIRED"
    assert not (tmp_path / storage_key).exists()
    session.commit.assert_awaited_once()
