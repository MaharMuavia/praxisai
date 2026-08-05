from typing import Any

PRIVATE_FIELDS = frozenset(
    {"student_email", "university", "accessibility", "reviewer_notes", "private_files"}
)


def public_credential_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in PRIVATE_FIELDS}
