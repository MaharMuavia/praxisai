from datetime import UTC, datetime

from app.credentials.service import (
    DemoSigningProvider,
    build_signed_credential,
    build_verification_qr_png,
    render_credential_pdf,
    verify_signed_credential,
)


def test_credential_signature_detects_tampering(tmp_path) -> None:
    signer = DemoSigningProvider(tmp_path / "private.pem")
    now = datetime.now(UTC)
    payload, digest, signature, slug = build_signed_credential(
        signer=signer,
        issuer="PraxisAI Demo",
        student_display_name="Demo Student",
        project_title="Private client project",
        role="Developer",
        contribution_summary="Implemented and tested the approved client workflow.",
        skill_evidence=[{"skill": "Testing", "criterion": "AC-1"}],
        verified_minutes=1_200,
        client_accepted_at=now,
        completed_at=now,
        public_artifacts=[],
        qa_summary="All approved acceptance criteria have evidence.",
        is_demo=True,
    )
    assert len(slug) >= 24
    assert verify_signed_credential(signer, payload, digest, signature)
    payload["verified_hours"] = "200.00"
    assert not verify_signed_credential(signer, payload, digest, signature)


def test_credential_pdf_and_qr_are_renderable_binary_documents() -> None:
    now = datetime.now(UTC).isoformat()
    payload = {
        "schema_version": "1.0",
        "credential_id": "demo-credential-id",
        "public_slug": "demo-public-slug",
        "issuer": "PraxisAI Demo",
        "student_display_name": "Demo Student",
        "project_title": "Private client project",
        "role": "student developer",
        "contribution_summary": "Implemented and validated the approved reporting workflow.",
        "skill_evidence": [
            {
                "evidence_id": "00000000-0000-0000-0000-000000000001",
                "skill": "Testing",
                "criterion": "Acceptance criterion 1",
                "summary": "Automated evidence confirms the approved workflow behavior.",
            }
        ],
        "verified_minutes": 1_200,
        "verified_hours": "20.00",
        "client_acceptance_timestamp": now,
        "completion_timestamp": now,
        "public_artifact_references": [],
        "qa_summary": "Passing QA is bound to the immutable artifact version.",
        "issued_timestamp": now,
        "status": "VALID",
        "environment": "demo",
        "key_identifier": "demo:test",
    }
    verification_url = "http://localhost:3000/verify/demo-public-slug"

    qr = build_verification_qr_png(verification_url)
    pdf = render_credential_pdf(
        payload=payload,
        verification_url=verification_url,
        status="VALID",
        signature_valid=True,
    )

    assert qr.startswith(b"\x89PNG\r\n\x1a\n")
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 5_000
