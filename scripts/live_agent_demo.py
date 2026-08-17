"""Run ONE real, live Gemini agent workflow (scoping) end to end and print the
recorded run — model id, token usage, latency, prompt version, input hash, and the
schema-enforced structured output.

This is the honest "AI is live in production" demonstration for the XPRIZE video and
product evidence. Unlike `npm run eval:agents` (which is deliberately fixture-only),
this hits the real GeminiAgentProvider.

Prerequisites (in the repo-root .env):
    GEMINI_PROVIDER=gemini
    GEMINI_API_KEY=<your key>      # or GOOGLE_CLOUD_PROJECT=<real project> for Vertex

Run:
    uv run --project apps/api python scripts/live_agent_demo.py
"""

import asyncio
import datetime
import json
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))

from app.agents.evaluation import EvaluationInput  # noqa: E402
from app.agents.prompts import prompt_for  # noqa: E402
from app.agents.provider import input_hash, provider_for  # noqa: E402
from app.config import Settings  # noqa: E402
from app.domain.schemas import ScopeDraft  # noqa: E402


async def main() -> None:
    settings = Settings()
    provider = provider_for(settings)
    prompt = prompt_for("scoping")

    print(f"provider : {settings.gemini_provider} | model: {settings.gemini_model}")
    print(f"class    : {type(provider).__name__}")
    if type(provider).__name__ != "GeminiAgentProvider":
        print("\nNOT LIVE. Set GEMINI_PROVIDER=gemini and a real key, then re-run.")
        return

    payload = EvaluationInput(
        title="Internal invoice-status dashboard",
        description=(
            "We are a 20-person logistics company. We need an internal, read-only web "
            "dashboard that reads our existing PostgreSQL 'invoices' table and shows "
            "outstanding, paid, and overdue totals by client, with a CSV export. It must "
            "load in under 2 seconds for 10k rows. Internal staff only, no public access."
        ),
    )

    corr = uuid.uuid4()
    started = time.time()
    output, metadata = await provider.generate_structured(
        agent_name=prompt.agent_name,
        prompt_version=prompt.version,
        system_instruction=prompt.system_instruction,
        input_payload=payload,
        output_schema=ScopeDraft,
        correlation_id=corr,
    )
    latency = round(time.time() - started, 2)

    print("\n=== LIVE GEMINI AGENT RUN — scoping ===")
    print(f"correlation_id : {corr}")
    print(f"input_hash     : {input_hash(payload)}")
    print(f"latency_seconds: {latency}")
    print(f"is_demo        : {metadata.get('is_demo')}")
    print(f"usage          : {metadata.get('usage')}")
    print(f"valid ScopeDraft (schema enforced): {isinstance(output, ScopeDraft)}")
    print("\n--- structured output ---")
    print(json.dumps(output.model_dump(), indent=2, default=str))

    evdir = REPO / "docs" / "evidence"
    evdir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "provider": settings.gemini_provider,
        "model": settings.gemini_model,
        "agent_name": prompt.agent_name,
        "prompt_version": prompt.version,
        "correlation_id": str(corr),
        "input_hash": input_hash(payload),
        "latency_seconds": latency,
        "metadata": {k: str(v) for k, v in dict(metadata).items()},
        "input": payload.model_dump(),
        "structured_output": output.model_dump(),
    }
    (evdir / "live-scoping-run.json").write_text(
        json.dumps(artifact, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nEvidence saved: {evdir / 'live-scoping-run.json'}")


if __name__ == "__main__":
    asyncio.run(main())
