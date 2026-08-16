import uuid

import pytest

from app.agents.provider import FixtureAgentProvider
from app.domain.schemas import PlanDraft, PlanInput, QADraft, QAInput


@pytest.mark.asyncio
async def test_fixture_plan_covers_every_acceptance_criterion() -> None:
    provider = FixtureAgentProvider()
    payload = PlanInput(
        project_title="Accessible reporting portal",
        scope_version_id=uuid.uuid4(),
        criterion_count=3,
    )

    plan, metadata = await provider.generate_structured(
        agent_name="planning",
        prompt_version="planning-v1",
        system_instruction="Propose only.",
        input_payload=payload,
        output_schema=PlanDraft,
        correlation_id=uuid.uuid4(),
    )

    covered = {
        ordinal
        for milestone in plan.milestones
        for task in milestone.tasks
        for ordinal in task.criterion_ordinals
    }
    assert covered == {1, 2, 3}
    assert metadata["is_demo"] is True


@pytest.mark.asyncio
async def test_fixture_qa_binds_one_result_to_each_criterion() -> None:
    provider = FixtureAgentProvider()
    payload = QAInput(
        artifact_id=uuid.uuid4(),
        artifact_kind="repository",
        artifact_uri="https://example.test/repository",
        artifact_content_hash="a" * 64,
        acceptance_criteria=["Keyboard navigation works", "Export is tenant scoped"],
    )

    review, _metadata = await provider.generate_structured(
        agent_name="qa",
        prompt_version="qa-v1",
        system_instruction="Review only.",
        input_payload=payload,
        output_schema=QADraft,
        correlation_id=uuid.uuid4(),
    )

    assert review.recommendation == "PASS"
    assert [item.criterion_ordinal for item in review.criterion_results] == [1, 2]
    assert all(item.evidence["artifact_hash_bound"] for item in review.criterion_results)


@pytest.mark.asyncio
async def test_fixture_multimodal_qa_evaluates_visual_and_criteria_evidence() -> None:
    from app.domain.schemas import MultimodalQADraft, MultimodalQAInput

    provider = FixtureAgentProvider()
    payload = MultimodalQAInput(
        artifact_id=uuid.uuid4(),
        artifact_kind="upload",
        artifact_uri="https://storage.praxisai.test/screenshots/dashboard.png",
        artifact_content_hash="b" * 64,
        mime_type="image/png",
        deliverable_title="Interactive Analytics Dashboard",
        acceptance_criteria=[
            "Navigation renders responsive sidebar across breakpoints",
            "Data visualizations show clear contrast and axis labels",
        ],
        rubric_focus=["layout", "accessibility", "responsive"],
    )

    review, metadata = await provider.generate_structured(
        agent_name="multimodal_qa",
        prompt_version="multimodal-qa-v1",
        system_instruction="Review visual and functional evidence.",
        input_payload=payload,
        output_schema=MultimodalQADraft,
        correlation_id=uuid.uuid4(),
        media_bytes=b"fake-png-binary-stream",
        media_mime_type="image/png",
    )

    assert review.recommendation == "PASS"
    assert review.overall_visual_score >= 90
    assert len(review.criterion_findings) == 2
    assert review.criterion_findings[0].passed is True
    assert review.criterion_findings[0].confidence_score > 0.9
    assert len(review.student_actionable_feedback) >= 1
    assert metadata["is_demo"] is True
    assert metadata["prompt_version"] == "multimodal-qa-v1"
