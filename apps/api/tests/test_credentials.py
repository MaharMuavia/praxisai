from datetime import UTC, datetime
from html import escape
from pathlib import Path

import pytest
from reportlab.platypus import Paragraph as ReportLabParagraph

from app.api.credentials import kms_verification_key_name
from app.credentials import service as credential_service
from app.credentials.service import (
    DemoSigningProvider,
    build_signed_credential,
    build_verification_qr_png,
    render_credential_pdf,
    verify_signed_credential,
)


def test_credential_signature_detects_tampering(tmp_path: Path) -> None:
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


def test_kms_rotation_allows_historical_versions_of_only_the_configured_key() -> None:
    configured = (
        "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
        "cryptoKeyVersions/7"
    )
    historical = (
        "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/issuer/"
        "cryptoKeyVersions/3"
    )

    assert kms_verification_key_name(configured, historical) == historical
    with pytest.raises(RuntimeError, match="not allowed"):
        kms_verification_key_name(
            configured,
            "projects/praxis/locations/global/keyRings/credentials/cryptoKeys/attacker/"
            "cryptoKeyVersions/3",
        )
    with pytest.raises(RuntimeError, match="not allowed"):
        kms_verification_key_name(configured, "projects/praxis/cryptoKeys/issuer")


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


def test_credential_pdf_escapes_all_dynamic_paragraph_markup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = "<b>FORGED</b>&#999999999999999999999999999999999;"
    now = datetime.now(UTC).isoformat()
    payload = {
        "credential_id": marker,
        "student_display_name": marker,
        "project_title": marker,
        "role": marker,
        "contribution_summary": marker,
        "skill_evidence": [
            {
                "skill": marker,
                "criterion": marker,
                "summary": marker,
            }
        ],
        "verified_hours": marker,
        "client_acceptance_timestamp": now,
        "completion_timestamp": now,
        "qa_summary": marker,
        "environment": marker,
    }
    paragraph_values: list[str] = []

    def recording_paragraph(value: str, *args: object, **kwargs: object) -> object:
        paragraph_values.append(value)
        return ReportLabParagraph(value, *args, **kwargs)

    monkeypatch.setattr(credential_service, "Paragraph", recording_paragraph)

    pdf = credential_service.render_credential_pdf(
        payload=payload,
        verification_url=f"https://example.test/verify/{marker}",
        status=marker,
        signature_valid=False,
    )

    assert pdf.startswith(b"%PDF-")
    assert paragraph_values
    assert all(marker not in value for value in paragraph_values)
    assert any(escape(marker) in value for value in paragraph_values)
