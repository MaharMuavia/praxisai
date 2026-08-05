from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AssignmentUnlock:
    state: str
    reason: str
    missing_requirements: tuple[str, ...]
    next_eligible_at: datetime | None


def evaluate_assignment_unlock(
    *,
    now: datetime,
    release_at: datetime,
    enrollment_active: bool,
    previous_week_complete: bool,
    required_units_complete: bool,
    quiz_passed: bool,
    prior_assignment_passed: bool,
    human_released: bool,
) -> AssignmentUnlock:
    missing: list[str] = []
    if not enrollment_active:
        missing.append("active enrollment")
    if now < release_at:
        return AssignmentUnlock(
            "LOCKED", "Release time has not arrived", tuple([*missing, "release time"]), release_at
        )
    if not previous_week_complete:
        missing.append("previous week complete")
    if not required_units_complete:
        missing.append("required units complete")
    if not quiz_passed:
        missing.append("quiz threshold")
    if not prior_assignment_passed:
        missing.append("prior assignment passed")
    if not human_released:
        missing.append("human release")
    return AssignmentUnlock(
        "AVAILABLE" if not missing else "LOCKED",
        "All unlock conditions are satisfied"
        if not missing
        else "Required conditions are incomplete",
        tuple(missing),
        None,
    )
