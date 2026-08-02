from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateInput:
    student_id: str
    active: bool
    eligible: bool
    suspended: bool
    conflict: bool
    available_hours: int
    required_hours: int
    workload_with_offer: int
    workload_cap: int
    skill_fit: int
    verified_evidence: int
    availability: int
    reliability: int
    complexity_readiness: int
    evidence_count: int


@dataclass(frozen=True)
class CandidateScore:
    student_id: str
    score_basis_points: int
    confidence: str
    components: dict[str, int]
    evidence_count: int


DEFAULT_WEIGHTS = {
    "skill_fit": 40,
    "verified_evidence": 20,
    "availability": 15,
    "reliability": 15,
    "complexity_readiness": 10,
}


def rank_candidates(
    candidates: list[CandidateInput], weights: dict[str, int] | None = None
) -> list[CandidateScore]:
    active_weights = weights or DEFAULT_WEIGHTS
    if set(active_weights) != set(DEFAULT_WEIGHTS) or sum(active_weights.values()) != 100:
        raise ValueError("Matching weights must contain the five documented factors and sum to 100")

    scored: list[CandidateScore] = []
    for candidate in candidates:
        if (
            not candidate.active
            or not candidate.eligible
            or candidate.suspended
            or candidate.conflict
        ):
            continue
        if candidate.available_hours < candidate.required_hours:
            continue
        if candidate.workload_with_offer > candidate.workload_cap:
            continue
        components = {
            "skill_fit": candidate.skill_fit,
            "verified_evidence": candidate.verified_evidence,
            "availability": candidate.availability,
            "reliability": candidate.reliability,
            "complexity_readiness": candidate.complexity_readiness,
        }
        if any(value < 0 or value > 100 for value in components.values()):
            raise ValueError("Matching factors must be between 0 and 100")
        score = sum(components[name] * active_weights[name] for name in active_weights)
        confidence = (
            "high"
            if candidate.evidence_count >= 4
            else "medium"
            if candidate.evidence_count >= 2
            else "low"
        )
        scored.append(
            CandidateScore(
                student_id=candidate.student_id,
                score_basis_points=score,
                confidence=confidence,
                components=components,
                evidence_count=candidate.evidence_count,
            )
        )
    return sorted(scored, key=lambda item: (-item.score_basis_points, item.student_id))
