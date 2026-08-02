import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.provider import AgentUnavailableError, GeminiAgentProvider
from app.config import Settings
from app.domain.schemas import ScopeDraft


class DummyPayload(ScopeDraft):
    pass


@pytest.mark.asyncio
async def test_gemini_adapter_mocked_success():
    settings = Settings(
        google_cloud_project="praxisai-test-project",
        google_cloud_location="us-central1",
        gemini_provider="gemini",
        app_env="test",
    )

    mock_response = MagicMock()
    mock_response.text = (
        '{"normalized_title":"Test Title","summary":"Summary","problem_statement":"Problem",'
        '"deliverables":["D1"],"acceptance_criteria":["AC1"],"assumptions":["A1"],'
        '"exclusions":["E1"],"dependencies":["Dep1"],"clarification_questions":[],'
        '"required_skills":["S1"],"effort_low_hours":10,"effort_high_hours":20,'
        '"complexity":"LOW","risk_items":[],"policy_flags":[],"manual_review_reasons":[],'
        '"confidence":"high","suggested_milestones":[]}'
    )
    mock_response.usage_metadata = None

    with patch("google.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client_instance

        provider = GeminiAgentProvider(settings)
        input_data = ScopeDraft(
            normalized_title="Test Title",
            summary="Summary",
            problem_statement="Problem",
            deliverables=["D1"],
            acceptance_criteria=["AC1"],
            assumptions=["A1"],
            exclusions=["E1"],
            dependencies=["Dep1"],
            clarification_questions=[],
            required_skills=["S1"],
            effort_low_hours=10,
            effort_high_hours=20,
            complexity="LOW",
            risk_items=[],
            policy_flags=[],
            manual_review_reasons=[],
            confidence="high",
            suggested_milestones=[],
        )

        output, metadata = await provider.generate_structured(
            agent_name="scope",
            prompt_version="v1",
            system_instruction="System prompt",
            input_payload=input_data,
            output_schema=ScopeDraft,
            correlation_id=uuid.uuid4(),
        )

        assert output.normalized_title == "Test Title"
        assert metadata["retry_count"] == 0
        assert metadata["stale_result_check"] is True
        assert "input_hash" in metadata


@pytest.mark.asyncio
async def test_gemini_adapter_bounded_retries_failure():
    settings = Settings(
        google_cloud_project="praxisai-test-project",
        google_cloud_location="us-central1",
        gemini_provider="gemini",
        app_env="test",
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("GCP error")
        )
        mock_client_cls.return_value = mock_client_instance

        provider = GeminiAgentProvider(settings)
        input_data = ScopeDraft(
            normalized_title="Test Title",
            summary="Summary",
            problem_statement="Problem",
            deliverables=["D1"],
            acceptance_criteria=["AC1"],
            assumptions=["A1"],
            exclusions=["E1"],
            dependencies=["Dep1"],
            clarification_questions=[],
            required_skills=["S1"],
            effort_low_hours=10,
            effort_high_hours=20,
            complexity="LOW",
            risk_items=[],
            policy_flags=[],
            manual_review_reasons=[],
            confidence="high",
            suggested_milestones=[],
        )

        with pytest.raises(AgentUnavailableError, match="bounded retries"):
            await provider.generate_structured(
                agent_name="scope",
                prompt_version="v1",
                system_instruction="System prompt",
                input_payload=input_data,
                output_schema=ScopeDraft,
                correlation_id=uuid.uuid4(),
            )
