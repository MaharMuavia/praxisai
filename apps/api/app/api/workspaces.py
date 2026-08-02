import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import DbSession, Principal, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.schemas import (
    ApprovalQueueItem,
    ClientInvoiceView,
    EarningsItemView,
    LeadReviewQueueItem,
    ProjectWorkspaceView,
    RiskQueueItem,
    StudentCredentialView,
)
from app.workspaces.service import (
    WorkspaceNotFound,
    approval_queue,
    client_invoices,
    lead_review_queue,
    participant_earnings,
    project_workspace,
    risk_queue,
    student_credentials,
)

router = APIRouter(tags=["role workspaces"])
ClientPrincipal = Annotated[
    SessionPrincipal, Depends(require_roles(Role.CLIENT_OWNER, Role.CLIENT_MEMBER))
]
StudentPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.STUDENT))]
ParticipantPrincipal = Annotated[
    SessionPrincipal, Depends(require_roles(Role.STUDENT, Role.TECHNICAL_LEAD))
]
LeadPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.TECHNICAL_LEAD))]
OperationsPrincipal = Annotated[
    SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN))
]


@router.get("/client/invoices", response_model=list[ClientInvoiceView])
async def invoices(principal: ClientPrincipal, session: DbSession) -> list[ClientInvoiceView]:
    return await client_invoices(session, principal=principal)


@router.get("/students/me/credentials", response_model=list[StudentCredentialView])
async def credentials(
    principal: StudentPrincipal, session: DbSession
) -> list[StudentCredentialView]:
    return await student_credentials(session, principal=principal)


@router.get("/participants/me/earnings", response_model=list[EarningsItemView])
async def earnings(principal: ParticipantPrincipal, session: DbSession) -> list[EarningsItemView]:
    return await participant_earnings(session, principal=principal)


@router.get("/leads/me/review-queue", response_model=list[LeadReviewQueueItem])
async def lead_reviews(principal: LeadPrincipal, session: DbSession) -> list[LeadReviewQueueItem]:
    return await lead_review_queue(session, principal=principal)


@router.get("/ops/approval-queue", response_model=list[ApprovalQueueItem])
async def approvals(principal: OperationsPrincipal, session: DbSession) -> list[ApprovalQueueItem]:
    return await approval_queue(session, principal=principal)


@router.get("/ops/risk-queue", response_model=list[RiskQueueItem])
async def risks(principal: OperationsPrincipal, session: DbSession) -> list[RiskQueueItem]:
    return await risk_queue(session, principal=principal)


@router.get("/projects/{project_id}/workspace", response_model=ProjectWorkspaceView)
async def project_command_center(
    project_id: uuid.UUID,
    principal: Principal,
    session: DbSession,
) -> ProjectWorkspaceView:
    try:
        return await project_workspace(
            session,
            project_id=project_id,
            principal=principal,
        )
    except WorkspaceNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
