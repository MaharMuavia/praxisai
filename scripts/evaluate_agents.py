"""Run the offline, fixture-only agent evaluation suite."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.agents.evaluation import evaluate_fixture_cases
from app.agents.provider import FixtureAgentProvider


async def main() -> None:
    # Keep the provider import/use explicit so this command cannot silently become live AI.
    if not isinstance(FixtureAgentProvider(), FixtureAgentProvider):
        raise RuntimeError("Deterministic evaluation requires the fixture provider")
    print(json.dumps(await evaluate_fixture_cases(), indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
