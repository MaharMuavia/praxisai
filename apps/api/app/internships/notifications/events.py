from typing import Final

INTERNSHIP_EVENTS: Final[frozenset[str]] = frozenset(
    {
        "application_saved",
        "application_submitted",
        "application_accepted",
        "application_rejected",
        "waitlisted",
        "cohort_starting",
        "week_unlocked",
        "assignment_released",
        "deadline_approaching",
        "submission_finalized",
        "review_assigned",
        "feedback_published",
        "changes_requested",
        "extension_decided",
        "completion_approved",
        "credential_issued",
        "credential_revoked",
    }
)
