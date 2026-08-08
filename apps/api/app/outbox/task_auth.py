import re
from typing import cast

from fastapi import HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import Settings


def task_url(settings: Settings) -> str:
    return f"{settings.api_base_url.rstrip('/')}/ops/tasks/process-outbox"


def verify_cloud_task_identity(request: Request, settings: Settings) -> None:
    """Require the configured Cloud Tasks service account in hosted environments."""
    if settings.app_env in {"local", "test"} and not settings.google_cloud_project:
        return
    authorization = request.headers.get("authorization", "")
    match = re.fullmatch(r"Bearer\s+(.+)", authorization, flags=re.IGNORECASE)
    if match is None or not settings.google_service_account_email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Cloud Tasks identity is required")
    try:
        claims = cast(
            dict[str, object],
            # google-auth does not ship type stubs for this verifier.
            id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                match.group(1),
                google_requests.Request(),
                audience=task_url(settings),
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Cloud Tasks identity is invalid"
        ) from exc
    if claims.get("email") != settings.google_service_account_email:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cloud Tasks service account is not allowed")
