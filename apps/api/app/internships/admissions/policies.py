from typing import Final

ACTIVE_APPLICATION_STATUSES: Final[frozenset[str]] = frozenset(
    {"DRAFT", "ELIGIBILITY_REVIEW", "SUBMITTED", "WAITLISTED", "ACCEPTED"}
)


def application_can_be_started(program_status: str, cohort_status: str) -> bool:
    return program_status in {"APPLICATIONS_OPEN", "ACTIVE"} and cohort_status in {
        "APPLICATIONS_OPEN",
        "ACTIVE",
    }


def decision_requires_track(decision: str) -> bool:
    return decision == "ACCEPTED"
