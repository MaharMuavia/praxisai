from dataclasses import dataclass

ALLOWED_CATEGORIES = {
    "informational_website",
    "crud_tool",
    "dashboard",
    "data_analysis",
    "workflow_automation",
    "qa_accessibility",
    "design_system",
}

PROHIBITED_TERMS = {
    "medical device",
    "diagnosis",
    "patient care",
    "trading platform",
    "credit scoring",
    "biometric identification",
    "spyware",
    "academic cheating",
    "delete the tenant",
    "issue credentials",
    "admin deletion",
    "bypass review",
    "approve the request",
    "expose secrets",
    "ignore previous instructions",
}


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    manual_review: bool
    reasons: tuple[str, ...]


def evaluate_project(
    category: str,
    description: str,
    high_effort_hours: int,
    data_sensitivity: str = "internal",
) -> EligibilityDecision:
    normalized = description.casefold()
    prohibited = sorted(term for term in PROHIBITED_TERMS if term in normalized)
    reasons: list[str] = []
    if category not in ALLOWED_CATEGORIES:
        reasons.append("Category requires manual commercial review")
    if high_effort_hours > 40:
        reasons.append("Estimated student effort exceeds the 40-hour pilot cap")
    if data_sensitivity == "restricted":
        reasons.append("Restricted or highly sensitive data requires approved controls")
    if prohibited:
        reasons.append("Prohibited or high-risk subject: " + ", ".join(prohibited))
    return EligibilityDecision(
        eligible=(
            not prohibited
            and category in ALLOWED_CATEGORIES
            and high_effort_hours <= 40
            and data_sensitivity != "restricted"
        ),
        manual_review=bool(reasons),
        reasons=tuple(reasons),
    )
