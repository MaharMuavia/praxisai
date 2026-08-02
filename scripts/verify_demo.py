import asyncio
import sys
from pathlib import Path

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.config import get_settings
from app.credentials.service import DemoSigningProvider, verify_signed_credential
from app.db import SessionFactory
from app.domain.models import (
    Approval,
    Credential,
    Deliverable,
    Invoice,
    Notification,
    PayoutAllocation,
    ProjectOpportunity,
    ProjectRisk,
    ProjectTransition,
    StudentProposal,
    Task,
    LearningPath,
)


async def verify_demo() -> None:
    settings = get_settings()
    if not (settings.is_local_or_test or settings.demo_mode):
        raise RuntimeError("Demo verification is refused outside local/test/demo")
    signer = DemoSigningProvider(settings.credential_demo_private_key_path)
    async with SessionFactory() as session:
        credential = await session.scalar(
            select(Credential).where(
                Credential.public_slug == "demo-accessible-resource-directory"
            )
        )
        if credential is None:
            raise RuntimeError("Seeded demo credential is missing")
        if not verify_signed_credential(
            signer,
            credential.canonical_payload,
            credential.payload_hash,
            credential.signature,
        ):
            raise RuntimeError("Seeded demo credential signature is invalid")
        expected_models = (
            Credential,
            Deliverable,
            Invoice,
            PayoutAllocation,
            ProjectRisk,
            Approval,
            Task,
            ProjectTransition,
            Notification,
            LearningPath,
            ProjectOpportunity,
            StudentProposal,
        )
        counts = {
            model.__name__: int(
                await session.scalar(select(func.count()).select_from(model)) or 0
            )
            for model in expected_models
        }
        missing = [name for name, count in counts.items() if count < 1]
        if missing:
            raise RuntimeError("Missing seeded demo records: " + ", ".join(missing))
    print(f"Verified demo lifecycle evidence: {counts}")
    print(f"Credential slug: {credential.public_slug}")


if __name__ == "__main__":
    asyncio.run(verify_demo())
