import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.auth import _set_session
from app.auth.dependencies import DbSession
from app.config import Settings, get_settings
from app.internships.schemas import (
    ProgramDetail,
    ProgramSummary,
    PublicCertificateView,
    SignupRequest,
    SignupResponse,
)
from app.internships.service import (
    Conflict,
    Forbidden,
    InternshipError,
    NotFound,
    list_programs,
    program_detail,
    public_certificate,
    signup,
)

router = APIRouter(prefix="/internships", tags=["internships public"])


def _raise(error: InternshipError) -> None:
    code = getattr(error, "code", "internship_error")
    status_code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(error, NotFound)
        else status.HTTP_409_CONFLICT
        if isinstance(error, Conflict)
        else status.HTTP_403_FORBIDDEN
        if isinstance(error, Forbidden)
        else status.HTTP_400_BAD_REQUEST
    )
    raise HTTPException(status_code, detail={"code": code, "message": str(error)}) from error


@router.get("/programs", response_model=list[ProgramSummary])
async def programs(session: DbSession) -> list[ProgramSummary]:
    return await list_programs(session)


@router.get("/certificates/{public_slug}", response_model=PublicCertificateView)
async def verify_certificate(public_slug: str, session: DbSession) -> PublicCertificateView:
    try:
        return await public_certificate(session, public_slug=public_slug)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/programs/{slug}", response_model=ProgramDetail)
async def program(slug: str, session: DbSession) -> ProgramDetail:
    try:
        return await program_detail(session, slug)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/programs/{program_id}/signup", response_model=SignupResponse, status_code=201)
async def student_signup(
    program_id: uuid.UUID,
    body: SignupRequest,
    request: Request,
    response: Response,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SignupResponse:
    try:
        result, application_id, principal = await signup(
            session,
            body=body,
            program_id=program_id,
            settings=settings,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    if principal is not None:
        await _set_session(response, principal, settings)
    if result == "CHECK_EMAIL":
        return SignupResponse(
            status="CHECK_EMAIL",
            message=(
                "If this verified identity is eligible, continue with the existing account session."
            ),
        )
    return SignupResponse(
        status="CREATED",
        message="Account provisioned. Complete the internship application before submission.",
        application_id=application_id,
    )
