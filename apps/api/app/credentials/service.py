import base64
import hashlib
import io
import json
import secrets
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import qrcode
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from google.cloud import kms
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class SigningProvider(Protocol):
    @property
    def key_identifier(self) -> str: ...

    def sign(self, payload: bytes) -> bytes: ...

    def verify(self, payload: bytes, signature: bytes) -> bool: ...


class DemoSigningProvider:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            loaded_key = serialization.load_pem_private_key(path.read_bytes(), password=None)
            if not isinstance(loaded_key, rsa.RSAPrivateKey):
                raise ValueError("Demo credential key must be an RSA private key")
            self._private_key: rsa.RSAPrivateKey = loaded_key
        else:
            self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            path.write_bytes(
                self._private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        public_der = self._private_key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self._key_identifier = "demo:" + hashlib.sha256(public_der).hexdigest()[:16]

    @property
    def key_identifier(self) -> str:
        return self._key_identifier

    def sign(self, payload: bytes) -> bytes:
        return self._private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())

    def verify(self, payload: bytes, signature: bytes) -> bool:
        try:
            self._private_key.public_key().verify(
                signature, payload, padding.PKCS1v15(), hashes.SHA256()
            )
            return True
        except ValueError:
            return False


class KmsSigningProvider:
    """RSA PKCS#1 SHA-256 signer backed by a configured Cloud KMS key version."""

    def __init__(self, key_version_name: str) -> None:
        self._client = kms.KeyManagementServiceClient()
        self._key_identifier = key_version_name
        public_key = self._client.get_public_key(request={"name": key_version_name})
        loaded_key = serialization.load_pem_public_key(public_key.pem.encode())
        if not isinstance(loaded_key, rsa.RSAPublicKey):
            raise ValueError("KMS credential key must be RSA")
        self._public_key: rsa.RSAPublicKey = loaded_key

    @property
    def key_identifier(self) -> str:
        return self._key_identifier

    def sign(self, payload: bytes) -> bytes:
        digest = hashlib.sha256(payload).digest()
        response = self._client.asymmetric_sign(
            request={"name": self._key_identifier, "digest": {"sha256": digest}}
        )
        return response.signature

    def verify(self, payload: bytes, signature: bytes) -> bool:
        try:
            self._public_key.verify(signature, payload, padding.PKCS1v15(), hashes.SHA256())
            return True
        except ValueError:
            return False


def build_signed_credential(
    *,
    signer: SigningProvider,
    issuer: str,
    student_display_name: str,
    project_title: str,
    role: str,
    contribution_summary: str,
    skill_evidence: list[dict[str, Any]],
    verified_minutes: int,
    client_accepted_at: datetime,
    completed_at: datetime,
    public_artifacts: list[dict[str, str]],
    qa_summary: str,
    is_demo: bool,
    credential_id: str | None = None,
    public_slug: str | None = None,
    issued_at: datetime | None = None,
) -> tuple[dict[str, Any], str, str, str]:
    issued_at = issued_at or datetime.now(UTC)
    credential_id = credential_id or secrets.token_urlsafe(18)
    public_slug = public_slug or secrets.token_urlsafe(24)
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "credential_id": credential_id,
        "public_slug": public_slug,
        "issuer": issuer,
        "student_display_name": student_display_name,
        "project_title": project_title,
        "role": role,
        "contribution_summary": contribution_summary,
        "skill_evidence": skill_evidence,
        "verified_minutes": verified_minutes,
        "verified_hours": f"{verified_minutes / 60:.2f}",
        "client_acceptance_timestamp": client_accepted_at.isoformat(),
        "completion_timestamp": completed_at.isoformat(),
        "public_artifact_references": public_artifacts,
        "qa_summary": qa_summary,
        "issued_timestamp": issued_at.isoformat(),
        "status": "VALID",
        "environment": "demo" if is_demo else "live",
        "key_identifier": signer.key_identifier,
    }
    encoded = canonical_json(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    signature = base64.b64encode(signer.sign(encoded)).decode()
    return payload, digest, signature, public_slug


def verify_signed_credential(
    signer: SigningProvider, payload: dict[str, Any], expected_hash: str, signature: str
) -> bool:
    encoded = canonical_json(payload)
    if not secrets.compare_digest(hashlib.sha256(encoded).hexdigest(), expected_hash):
        return False
    try:
        decoded_signature = base64.b64decode(signature, validate=True)
    except ValueError:
        return False
    return signer.verify(encoded, decoded_signature)


def build_verification_qr_png(verification_url: str) -> bytes:
    parsed = urlparse(verification_url)
    is_local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    if not parsed.hostname or (parsed.scheme != "https" and not is_local_http):
        raise ValueError("Verification URL must use HTTPS, except for localhost")
    if len(verification_url) > 2_000:
        raise ValueError("Verification URL is too long")
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#081923", back_color="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def render_credential_pdf(
    *,
    payload: dict[str, Any],
    verification_url: str,
    status: str,
    signature_valid: bool,
) -> bytes:
    qr_png = build_verification_qr_png(verification_url)
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="PraxisAI Verified Project Credential",
        author="PraxisAI",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CredentialTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#081923"),
        spaceAfter=6 * mm,
    )
    centered_style = ParagraphStyle(
        "CredentialCentered",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#34515F"),
        fontSize=9,
        leading=12,
    )
    status_style = ParagraphStyle(
        "CredentialStatus",
        parent=centered_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    body_style = ParagraphStyle(
        "CredentialBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#193640"),
    )
    label_style = ParagraphStyle(
        "CredentialLabel",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#081923"),
    )

    def text_value(key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str | int):
            raise ValueError(f"Credential field {key} is malformed")
        return escape(str(value))

    environment = text_value("environment").upper()
    status_color = colors.HexColor("#147D64") if status == "VALID" else colors.HexColor("#A12B3A")
    story: list[Any] = [
        Paragraph("PraxisAI Verified Project Credential", title_style),
        Table(
            [
                [
                    Paragraph(escape(status), status_style),
                    Paragraph(
                        "SIGNATURE VERIFIED" if signature_valid else "SIGNATURE INVALID",
                        centered_style,
                    ),
                    Paragraph(f"{environment} ENVIRONMENT", centered_style),
                ]
            ],
            colWidths=[52 * mm, 52 * mm, 52 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), status_color),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                    ("BACKGROUND", (1, 0), (2, 0), colors.HexColor("#E8F4F2")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8CED2")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8CED2")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        ),
        Spacer(1, 8 * mm),
        Paragraph("Awarded to", label_style),
        Paragraph(text_value("student_display_name"), title_style),
        Paragraph(
            f"For verified work as <b>{text_value('role')}</b> on "
            f"<b>{text_value('project_title')}</b>.",
            body_style,
        ),
        Spacer(1, 4 * mm),
        Paragraph(text_value("contribution_summary"), body_style),
        Spacer(1, 6 * mm),
        Table(
            [
                [Paragraph("Verified hours", label_style), text_value("verified_hours")],
                [
                    Paragraph("Client accepted", label_style),
                    text_value("client_acceptance_timestamp"),
                ],
                [Paragraph("Completed", label_style), text_value("completion_timestamp")],
                [Paragraph("Credential ID", label_style), text_value("credential_id")],
            ],
            colWidths=[45 * mm, 111 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF5F4")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8CED2")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6E3E5")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 6 * mm),
        Paragraph("Quality evidence", label_style),
        Paragraph(text_value("qa_summary"), body_style),
        Spacer(1, 5 * mm),
        Paragraph("Verified skills", label_style),
    ]
    raw_evidence = payload.get("skill_evidence")
    if not isinstance(raw_evidence, list) or not raw_evidence:
        raise ValueError("Credential skill evidence is malformed")
    for item in raw_evidence:
        if not isinstance(item, dict):
            raise ValueError("Credential skill evidence is malformed")
        skill = item.get("skill")
        criterion = item.get("criterion")
        summary = item.get("summary")
        if not isinstance(skill, str) or not skill:
            raise ValueError("Credential skill evidence is malformed")
        if not isinstance(criterion, str) or not criterion:
            raise ValueError("Credential skill evidence is malformed")
        if not isinstance(summary, str) or not summary:
            raise ValueError("Credential skill evidence is malformed")
        story.append(
            Paragraph(
                f"<b>{escape(skill)}</b> - {escape(criterion)}: {escape(summary)}",
                body_style,
            )
        )
        story.append(Spacer(1, 2 * mm))
    qr_stream = io.BytesIO(qr_png)
    story.extend(
        [
            Spacer(1, 4 * mm),
            Table(
                [
                    [
                        Image(qr_stream, width=32 * mm, height=32 * mm),
                        Paragraph(
                            "Scan to verify the current signature and revocation status.<br/>"
                            f"{escape(verification_url)}",
                            body_style,
                        ),
                    ]
                ],
                colWidths=[40 * mm, 116 * mm],
                style=TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]),
            ),
        ]
    )

    def add_footer(canvas: Canvas, _document: SimpleDocTemplate) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#5B737C"))
        canvas.drawString(20 * mm, 10 * mm, "PraxisAI - evidence-backed project credential")
        canvas.drawRightString(190 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    document.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return output.getvalue()
