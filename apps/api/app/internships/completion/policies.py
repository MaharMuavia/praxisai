from dataclasses import dataclass


@dataclass(frozen=True)
class CompletionEligibility:
    eligible: bool
    missing: tuple[str, ...]


def evaluate_completion_gates(**gates: bool) -> CompletionEligibility:
    missing = tuple(name for name, passed in gates.items() if not passed)
    return CompletionEligibility(not missing, missing)
