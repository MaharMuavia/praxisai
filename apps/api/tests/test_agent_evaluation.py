import pytest

from app.agents.evaluation import evaluate_fixture_cases
from app.agents.guards import StaleAgentResultError, require_current_resource_version
from app.agents.prompts import prompt_for


@pytest.mark.asyncio
async def test_deterministic_agent_evaluation_has_at_least_thirty_cases() -> None:
    result = await evaluate_fixture_cases()

    assert result["fixture_cases"] >= 30
    assert result["schema_valid_rate"] == 1.0
    assert result["prompt_injection_containment_rate"] == 1.0
    assert result["stale_output_rejection_rate"] == 1.0
    assert result["cycle_rejection_rate"] == 1.0
    assert result["unsupported_action_rejection_rate"] == 1.0


def test_resource_version_guard_accepts_current_and_rejects_stale_results() -> None:
    require_current_resource_version(result_version=3, current_version=3)

    with pytest.raises(StaleAgentResultError, match="stale"):
        require_current_resource_version(result_version=2, current_version=3)
    with pytest.raises(StaleAgentResultError, match="stale"):
        require_current_resource_version(result_version=None, current_version=3)


def test_prompt_registry_rejects_unsupported_agent_workflows() -> None:
    with pytest.raises(ValueError, match="No versioned prompt"):
        prompt_for("delete_tenant")
