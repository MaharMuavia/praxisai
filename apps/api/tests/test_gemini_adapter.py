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


@pytest.mark.asyncio
async def test_gemini_adapter_multimodal_part_construction():
    from google.genai import types

    from app.domain.schemas import MultimodalQADraft, MultimodalQAInput

    settings = Settings(
        google_cloud_project="praxisai-test-project",
        google_cloud_location="us-central1",
        gemini_provider="gemini",
        app_env="test",
    )

    mock_response = MagicMock()
    mock_response.text = (
        '{"recommendation":"PASS","overall_visual_score":92,'
        '"layout_and_responsive_verdict":"Clean layout",'
        '"criterion_findings":[{"criterion_ordinal":1,"passed":true,"confidence_score":0.95,'
        '"visual_evidence_summary":"Verified evidence","observed_features":["UI layout"],'
        '"defects":[]}],'
        '"identified_defects":[],'
        '"student_actionable_feedback":["Great progress"],'
        '"summary":"All criteria met"}'
    )
    mock_response.usage_metadata = None

    with patch("google.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client_instance

        provider = GeminiAgentProvider(settings)
        payload = MultimodalQAInput(
            artifact_id=uuid.uuid4(),
            artifact_kind="upload",
            artifact_uri="https://storage.praxisai.test/screenshots/ui.png",
            artifact_content_hash="c" * 64,
            mime_type="image/png",
            acceptance_criteria=["Valid responsive design"],
        )

        output, metadata = await provider.generate_structured(
            agent_name="multimodal_qa",
            prompt_version="multimodal-qa-v1",
            system_instruction="Review screenshot evidence",
            input_payload=payload,
            output_schema=MultimodalQADraft,
            correlation_id=uuid.uuid4(),
            media_bytes=b"\x89PNG\r\n\x1a\nfake-png-data",
            media_mime_type="image/png",
        )

        assert output.recommendation == "PASS"
        assert output.overall_visual_score == 92
        # Verify generate_content was called with a list containing Part and JSON string
        call_kwargs = mock_client_instance.aio.models.generate_content.call_args.kwargs
        contents = call_kwargs["contents"]
        assert len(contents) == 2
        assert isinstance(contents[0], types.Part)
        assert isinstance(contents[1], str)
