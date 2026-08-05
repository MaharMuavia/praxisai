from typing import Any


def missing_required_evidence(
    requirements: list[dict[str, Any]],
    *,
    links: dict[str, str],
    text_fields: dict[str, str],
    artifact_types: set[str],
) -> list[str]:
    supplied = set(links) | set(text_fields) | artifact_types
    return [
        str(item.get("type", "artifact"))
        for item in requirements
        if item.get("required", True) and str(item.get("type")) not in supplied
    ]
