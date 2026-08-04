from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    AllowedStudentEmail,
    InternshipApplication,
    InternshipCohort,
    InternshipProgram,
    UniversityEmailDomain,
)

DISPOSABLE_EMAIL_DOMAINS = frozenset(
    {"mailinator.com", "guerrillamail.com", "10minutemail.com", "yopmail.com"}
)


def normalize_email(value: str) -> str:
    try:
        return validate_email(value, check_deliverability=False).normalized.casefold()
    except EmailNotValidError as exc:
        raise ValueError("Email address is invalid") from exc


def normalize_domain(value: str) -> str:
    candidate = value.strip().rstrip(".").casefold()
    if not candidate:
        raise ValueError("Email domain is required")
    try:
        return candidate.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("Email domain is invalid") from exc


def email_domain(email: str) -> str:
    return normalize_email(email).rsplit("@", 1)[1]


def domain_matches(
    *, email_domain_value: str, approved_domain: str, allow_subdomains: bool
) -> bool:
    normalized_email_domain = normalize_domain(email_domain_value)
    normalized_approved_domain = normalize_domain(approved_domain)
    return normalized_email_domain == normalized_approved_domain or (
        allow_subdomains and normalized_email_domain.endswith("." + normalized_approved_domain)
    )


@dataclass(frozen=True)
class EmailEligibility:
    eligible: bool
    reason: str
    university_id: UUID | None = None
    requires_review: bool = False


async def evaluate_email_eligibility(
    session: AsyncSession,
    *,
    email: str,
    program: InternshipProgram,
    cohort: InternshipCohort,
) -> EmailEligibility:
    normalized = normalize_email(email)
    domain = email_domain(normalized)
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return EmailEligibility(False, "DISPOSABLE_DOMAIN")

    invite = await session.scalar(
        select(AllowedStudentEmail).where(
            AllowedStudentEmail.cohort_id == cohort.id,
            AllowedStudentEmail.email == normalized,
            AllowedStudentEmail.status == "ACTIVE",
        )
    )
    now = datetime.now(UTC)
    if invite and (invite.expires_at is None or invite.expires_at > now):
        return EmailEligibility(True, "INVITED")

    rows = (
        await session.execute(
            select(UniversityEmailDomain).where(UniversityEmailDomain.status == "APPROVED")
        )
    ).scalars()
    for approved in rows:
        if domain_matches(
            email_domain_value=domain,
            approved_domain=approved.domain,
            allow_subdomains=approved.allow_subdomains,
        ):
            return EmailEligibility(True, "APPROVED_UNIVERSITY_DOMAIN", approved.university_id)

    if program.personal_email_exception_policy == "REVIEW":
        return EmailEligibility(True, "PERSONAL_EMAIL_REVIEW", requires_review=True)
    return EmailEligibility(False, "INVITATION_OR_APPROVED_DOMAIN_REQUIRED")


def is_application_complete(application: InternshipApplication) -> bool:
    required_text = (
        application.primary_track_id,
        (application.education_status or "").strip(),
        (application.degree_program or "").strip(),
        (application.country or "").strip(),
        (application.technical_background or "").strip(),
        (application.motivation or "").strip(),
    )
    return all(required_text) and application.weekly_availability_hours is not None
