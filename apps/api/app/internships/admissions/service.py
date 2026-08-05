from dataclasses import dataclass

from .policies import application_can_be_started


@dataclass(frozen=True)
class AdmissionTransition:
    status: str
    requires_human_review: bool


def initial_application_transition(
    *, program_status: str, cohort_status: str, requires_human_review: bool
) -> AdmissionTransition:
    if not application_can_be_started(program_status, cohort_status):
        raise ValueError("Applications are not open for this cohort")
    return AdmissionTransition(
        status="ELIGIBILITY_REVIEW" if requires_human_review else "DRAFT",
        requires_human_review=requires_human_review,
    )
