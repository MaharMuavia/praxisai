from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import DbSession, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import Role
from app.internships.schemas import UploadCompleteRequest, UploadInitiateRequest, UploadView
from app.internships.service import (
    InternshipError,
    complete_upload,
    get_upload_status,
    initiate_upload,
    receive_upload_stream,
)

router = APIRouter(prefix="/internships/uploads", tags=["internship uploads"])
UploadPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.STUDENT))]


def _raise(error: InternshipError) -> None:
    if error.code == "not_found":
        code = status.HTTP_404_NOT_FOUND
    elif error.code == "storage_unavailable":
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(code, detail={"code": error.code, "message": str(error)}) from error


@router.post("/initiate", response_model=UploadView, status_code=201)
async def initiate(
    body: UploadInitiateRequest,
    principal: UploadPrincipal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadView:
    try:
        return await initiate_upload(session, principal=principal, body=body, settings=settings)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/{upload_id}", response_model=UploadView)
async def status_view(
    upload_id: str,
    principal: UploadPrincipal,
    session: DbSession,
) -> UploadView:
    try:
        return await get_upload_status(session, principal=principal, upload_id=upload_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.put("/{upload_id}/content", response_model=UploadView)
async def upload_content(
    upload_id: str,
    request: Request,
    principal: UploadPrincipal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadView:
    content_length = request.headers.get("content-length")
    try:
        content_length_value = int(content_length) if content_length else None
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Content-Length") from exc
    if content_length_value is not None and content_length_value < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Content-Length")
    if (
        content_length_value is not None
        and content_length_value > settings.internship_max_upload_bytes
    ):
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Upload exceeds the package limit"
        )
    try:
        return await receive_upload_stream(
            session,
            principal=principal,
            upload_id=upload_id,
            chunks=request.stream(),
            settings=settings,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/{upload_id}/complete", response_model=UploadView)
async def complete(
    upload_id: str,
    body: UploadCompleteRequest,
    principal: UploadPrincipal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadView:
    try:
        return await complete_upload(
            session,
            principal=principal,
            upload_id=upload_id,
            body=body,
            settings=settings,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")
