import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.credentials.service import render_credential_pdf


def main() -> None:
    output_path = ROOT / "output" / "pdf" / "praxisai-demo-credential.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "credential_id": "DEMO-CREDENTIAL-NOT-FOR-PRODUCTION",
        "public_slug": "demo-credential-preview",
        "issuer": "PraxisAI Demo",
        "student_display_name": "Amina Noor (Fictional)",
        "project_title": "Private client project",
        "role": "student developer",
        "contribution_summary": (
            "Implemented the approved reporting workflow and supplied automated "
            "acceptance evidence for coordinator review."
        ),
        "skill_evidence": [
            {
                "evidence_id": "00000000-0000-0000-0000-000000000001",
                "skill": "Accessible frontend engineering",
                "criterion": "Keyboard workflow acceptance criterion",
                "summary": (
                    "Automated and human-reviewed evidence confirms keyboard access "
                    "through the primary workflow."
                ),
            },
            {
                "evidence_id": "00000000-0000-0000-0000-000000000002",
                "skill": "Test automation",
                "criterion": "Primary workflow completion criterion",
                "summary": (
                    "Persisted test evidence covers the approved workflow and tenant boundary."
                ),
            },
        ],
        "verified_minutes": 1_200,
        "verified_hours": "20.00",
        "client_acceptance_timestamp": "2026-07-30T10:00:00+00:00",
        "completion_timestamp": "2026-07-30T12:00:00+00:00",
        "public_artifact_references": [],
        "qa_summary": (
            "Passing QA is bound to the immutable demo artifact; deterministic "
            "evidence checks passed."
        ),
        "issued_timestamp": "2026-07-30T12:05:00+00:00",
        "status": "VALID",
        "environment": "demo",
        "key_identifier": "demo:preview-only",
    }
    content = render_credential_pdf(
        payload=payload,
        verification_url="http://localhost:3000/verify/demo-credential-preview",
        status="VALID",
        signature_valid=True,
    )
    output_path.write_bytes(content)
    print(output_path)


if __name__ == "__main__":
    main()
