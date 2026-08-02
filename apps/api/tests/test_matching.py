from app.staffing.service import CandidateInput, rank_candidates


def candidate(
    student_id: str,
    *,
    suspended: bool = False,
    available_hours: int = 20,
    workload_with_offer: int = 15,
) -> CandidateInput:
    return CandidateInput(
        student_id=student_id,
        active=True,
        eligible=True,
        suspended=suspended,
        conflict=False,
        available_hours=available_hours,
        required_hours=10,
        workload_with_offer=workload_with_offer,
        workload_cap=20,
        skill_fit=80,
        verified_evidence=70,
        availability=90,
        reliability=80,
        complexity_readiness=60,
        evidence_count=3,
    )


def test_matching_filters_ineligible_and_orders_ties_stably() -> None:
    results = rank_candidates(
        [candidate("b"), candidate("a"), candidate("suspended", suspended=True)]
    )
    assert [result.student_id for result in results] == ["a", "b"]
    assert results[0].score_basis_points == 7_750
    assert results[0].confidence == "medium"


def test_matching_excludes_unavailable_and_overloaded_students() -> None:
    results = rank_candidates(
        [
            candidate("unavailable", available_hours=5),
            candidate("overloaded", workload_with_offer=21),
        ]
    )
    assert results == []
