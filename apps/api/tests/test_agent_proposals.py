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
