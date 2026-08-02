import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import DbSession, IdempotencyKey, correlation_id, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.schemas import (
    EmployerOpportunityView,
    OpportunityPublishRequest,
    OpportunityView,
    ProposalDecisionRequest,
    StudentProposalCreate,
    StudentProposalView,
)
from app.talent.service import (
    TalentError,
    TalentNotFound,
    decide_proposal,
    list_employer_opportunities,
    list_student_opportunities,
    list_student_proposals,
    publish_opportunity,
    submit_proposal,
)

router = APIRouter(prefix="/talent", tags=["talent marketplace"])
StudentPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.STUDENT))]
EmployerPrincipal = Annotated[
    SessionPrincipal, Depends(require_roles(Role.CLIENT_OWNER, Role.CLIENT_MEMBER))
]
EmployerOwnerPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.CLIENT_OWNER))]


@router.get("/opportunities", response_model=list[OpportunityView])
async def opportunities(principal: StudentPrincipal, session: DbSession) -> list[OpportunityView]:
    return await list_student_opportunities(session, principal=principal)


@router.get("/students/me/proposals", response_model=list[StudentProposalView])
async def student_proposals(
    principal: StudentPrincipal, session: DbSession
) -> list[StudentProposalView]:
    return await list_student_proposals(session, principal=principal)


@router.post(
    "/opportunities/{opportunity_id}/proposals",
    response_model=StudentProposalView,
    status_code=status.HTTP_201_CREATED,
)
async def create_proposal(
    opportunity_id: uuid.UUID,
    body: StudentProposalCreate,
    principal: StudentPrincipal,
    session: DbSession,
    key: IdempotencyKey,
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> StudentProposalView:
    try:
        return await submit_proposal(
            session,
            opportunity_id=opportunity_id,
            body=body,
            principal=principal,
            idempotency_key=key,
            correlation_id=request_correlation_id,
        )
    except TalentNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except TalentError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.get("/employers/me/opportunities", response_model=list[EmployerOpportunityView])
async def employer_opportunities(
    principal: EmployerPrincipal, session: DbSession
) -> list[EmployerOpportunityView]:
    return await list_employer_opportunities(session, principal=principal)


@router.post(
    "/employers/me/opportunities",
    response_model=EmployerOpportunityView,
    status_code=status.HTTP_201_CREATED,
)
async def create_opportunity(
    body: OpportunityPublishRequest,
    principal: EmployerOwnerPrincipal,
    session: DbSession,
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> EmployerOpportunityView:
    try:
        return await publish_opportunity(
            session,
            body=body,
            principal=principal,
            correlation_id=request_correlation_id,
        )
    except TalentNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except TalentError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/proposals/{proposal_id}/decision", response_model=StudentProposalView)
async def proposal_decision(
    proposal_id: uuid.UUID,
    body: ProposalDecisionRequest,
    principal: EmployerOwnerPrincipal,
    session: DbSession,
    key: IdempotencyKey,
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> StudentProposalView:
    try:
        return await decide_proposal(
            session,
            proposal_id=proposal_id,
            body=body,
            principal=principal,
            idempotency_key=key,
            correlation_id=request_correlation_id,
        )
    except TalentNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except TalentError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
