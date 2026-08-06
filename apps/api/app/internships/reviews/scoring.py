from typing import Any


class RubricValidationError(ValueError):
    """A review rubric is structurally invalid or incomplete."""


def weighted_score(scores: list[dict[str, Any]], rubric: list[dict[str, Any]]) -> int:
    criteria: dict[str, dict[str, Any]] = {}
    for item in rubric:
        criterion_id = str(item.get("id", ""))
        if not criterion_id or criterion_id in criteria:
            raise RubricValidationError("Rubric criteria must have unique identifiers")
        criteria[criterion_id] = item
    if not criteria:
        raise RubricValidationError("Assignment rubric is empty")
    seen: set[str] = set()
    total = 0.0
    for score in scores:
        criterion_id = str(score.get("criterion_id", ""))
        criterion = criteria.get(criterion_id)
        if criterion is None:
            raise RubricValidationError("Review contains an unknown rubric criterion")
        if criterion_id in seen:
            raise RubricValidationError("Review contains a duplicate rubric criterion")
        seen.add(criterion_id)
        maximum = float(criterion.get("max_score", 0))
        weight = float(criterion.get("weight", 0))
        value = float(score.get("score", -1))
        if maximum <= 0 or weight <= 0 or value < 0 or value > maximum:
            raise RubricValidationError("Rubric score is outside the allowed range")
        total += value / maximum * weight
    if set(criteria) - seen:
        raise RubricValidationError("Review is missing required rubric criteria")
    if abs(sum(float(item.get("weight", 0)) for item in criteria.values()) - 100) > 0.01:
        raise RubricValidationError("Rubric weights must total 100")
    return round(total)
