import asyncio
import hashlib
import json
import time
import uuid
from typing import Protocol, TypedDict, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import Settings
from app.domain.schemas import (
    PlanDraft,
    PlanMilestoneDraft,
    PlanTaskDraft,
    QACriterionResult,
    QADraft,
    ScopeDraft,
)

OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentMetadata(TypedDict):
    model: str
    usage: dict[str, object] | None
    latency_ms: int
    is_demo: bool
    retry_count: int
    prompt_version: str
    input_hash: str
    correlation_id: str
    stale_result_check: bool


class AgentUnavailableError(RuntimeError):
    pass


class AgentProvider(Protocol):
    async def generate_structured(
        self,
        *,
        agent_name: str,
        prompt_version: str,
        system_instruction: str,
        input_payload: BaseModel,
        output_schema: type[OutputT],
        correlation_id: uuid.UUID,
    ) -> tuple[OutputT, AgentMetadata]: ...


class DisabledAgentProvider:
    async def generate_structured(
        self,
        *,
        agent_name: str,
        prompt_version: str,
        system_instruction: str,
        input_payload: BaseModel,
        output_schema: type[OutputT],
        correlation_id: uuid.UUID,
    ) -> tuple[OutputT, AgentMetadata]:
        raise AgentUnavailableError(
            "AI actions are disabled. Configure Gemini or explicitly enable demo fixture mode."
        )


class FixtureAgentProvider:
    async def generate_structured(
        self,
        *,
        agent_name: str,
        prompt_version: str,
        system_instruction: str,
        input_payload: BaseModel,
        output_schema: type[OutputT],
        correlation_id: uuid.UUID,
    ) -> tuple[OutputT, AgentMetadata]:
        raw = input_payload.model_dump()
        payload_hash = input_hash(input_payload)
        if output_schema is PlanDraft:
            criterion_count = int(raw.get("criterion_count", 1))
            plan = PlanDraft(
                milestones=[
                    PlanMilestoneDraft(
                        title="Build and validate",
                        due_offset_days=14,
                        tasks=[
                            PlanTaskDraft(
                                title="Implement approved acceptance criteria",
                                definition_of_done=(
                                    "Every approved criterion has implementation "
                                    "and review evidence."
                                ),
                                criterion_ordinals=list(range(1, criterion_count + 1)),
                                estimate_hours=12,
                                dependency_titles=[],
                            ),
                            PlanTaskDraft(
                                title="Prepare delivery evidence",
                                definition_of_done=(
                                    "The immutable artifact version and deterministic "
                                    "evidence are recorded."
                                ),
                                criterion_ordinals=list(range(1, criterion_count + 1)),
                                estimate_hours=4,
                                dependency_titles=["Implement approved acceptance criteria"],
                            ),
                        ],
                    )
                ],
                risks=["Required client access may delay evidence collection"],
            )
            return output_schema.model_validate(plan.model_dump()), {
                "model": "fixture/planning-v1",
                "usage": None,
                "latency_ms": 0,
                "is_demo": True,
                "retry_count": 0,
                "prompt_version": prompt_version,
                "input_hash": payload_hash,
                "correlation_id": str(correlation_id),
                "stale_result_check": True,
            }
        if output_schema is QADraft:
            criteria = list(raw.get("acceptance_criteria", []))
            qa = QADraft(
                recommendation="PASS",
                criterion_results=[
                    QACriterionResult(
                        criterion_ordinal=ordinal,
                        passed=True,
                        summary="Fixture review found evidence aligned to this criterion.",
                        evidence={"source": "fixture", "artifact_hash_bound": True},
                    )
                    for ordinal, _criterion in enumerate(criteria, start=1)
                ],
                summary="All criteria have fixture review evidence bound to this artifact version.",
            )
            return output_schema.model_validate(qa.model_dump()), {
                "model": "fixture/qa-v1",
                "usage": None,
                "latency_ms": 0,
                "is_demo": True,
                "retry_count": 0,
                "prompt_version": prompt_version,
                "input_hash": payload_hash,
                "correlation_id": str(correlation_id),
                "stale_result_check": True,
            }
        if output_schema is not ScopeDraft:
            raise AgentUnavailableError(
                f"No demo fixture is registered for {output_schema.__name__}"
            )
        title = str(raw.get("title", "Client project"))
        output = ScopeDraft(
            normalized_title=title.strip(),
            summary=f"A constrained delivery engagement for {title.strip()}.",
            problem_statement=str(raw.get("description", "")),
            deliverables=["Working implementation", "Deployment and handoff documentation"],
            acceptance_criteria=[
                "The primary workflow completes without an unhandled error",
                "The delivered interface meets the approved responsive requirements",
            ],
            assumptions=["The client supplies required content and access before work starts"],
            exclusions=["Ongoing support and unlisted integrations"],
            dependencies=["Approved scope", "Confirmed external funding evidence"],
            clarification_questions=[],
            required_skills=["TypeScript", "Web accessibility", "Testing"],
            effort_low_hours=16,
            effort_high_hours=28,
            complexity="MEDIUM",
            risk_items=["External access may delay validation"],
            policy_flags=[],
            manual_review_reasons=[],
            confidence="medium",
            suggested_milestones=["Foundation", "Implementation", "QA and handoff"],
        )
        return output_schema.model_validate(output.model_dump()), {
            "model": "fixture/scoping-v1",
            "usage": None,
            "latency_ms": 0,
            "is_demo": True,
            "retry_count": 0,
            "prompt_version": prompt_version,
            "input_hash": payload_hash,
            "correlation_id": str(correlation_id),
            "stale_result_check": True,
        }


class GeminiAgentProvider:
    def __init__(self, settings: Settings) -> None:
        if settings.google_cloud_project:
            self._client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
        elif settings.gemini_api_key:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        else:
            raise AgentUnavailableError("Gemini credentials are not configured")
        self._model = settings.gemini_model

    async def generate_structured(
        self,
        *,
        agent_name: str,
        prompt_version: str,
        system_instruction: str,
        input_payload: BaseModel,
        output_schema: type[OutputT],
        correlation_id: uuid.UUID,
    ) -> tuple[OutputT, AgentMetadata]:
        started = time.perf_counter()
        response = None
        retry_count = 0
        payload_hash = input_hash(input_payload)
        for attempt in range(3):
            try:
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self._model,
                        contents=json.dumps(
                            input_payload.model_dump(mode="json"), separators=(",", ":")
                        ),
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=output_schema,
                            temperature=0.1,
                        ),
                    ),
                    timeout=30.0,
                )
                break
            except Exception as exc:
                if attempt == 2:
                    raise AgentUnavailableError(
                        "Gemini request failed after bounded retries"
                    ) from exc
                retry_count += 1
                await asyncio.sleep(0.25 * (2**attempt))
        if response is None:
            raise AgentUnavailableError("Gemini returned no response")
        if not response.text:
            raise AgentUnavailableError("Gemini returned no structured output")
        output = output_schema.model_validate_json(response.text)
        usage: dict[str, object] | None = (
            response.usage_metadata.model_dump() if response.usage_metadata else None
        )
        return output, {
            "model": self._model,
            "usage": usage,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "is_demo": False,
            "retry_count": retry_count,
            "prompt_version": prompt_version,
            "input_hash": payload_hash,
            "correlation_id": str(correlation_id),
            "stale_result_check": True,
        }


def input_hash(payload: BaseModel) -> str:
    encoded = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def provider_for(settings: Settings) -> AgentProvider:
    if settings.gemini_provider == "disabled":
        return DisabledAgentProvider()
    if settings.gemini_provider == "fixture":
        if not (settings.is_local_or_test or settings.demo_mode):
            raise AgentUnavailableError("Fixture AI is prohibited in this environment")
        return FixtureAgentProvider()
    return GeminiAgentProvider(settings)
