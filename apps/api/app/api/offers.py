import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.auth.dependencies import DbSession, IdempotencyKey, Principal
from app.domain.models import AssignmentOffer
from app.domain.schemas import OfferDecisionRequest, OfferView
from app.offers.service import OfferError, decide_offer

router = APIRouter(prefix="/assignment-offers", tags=["offers"])


@router.get("", response_model=list[OfferView])
async def list_offers(principal: Principal, session: DbSession) -> list[AssignmentOffer]:
    return list(
        (
            await session.scalars(
                select(AssignmentOffer)
                .where(AssignmentOffer.recipient_user_id == principal.user_id)
                .order_by(AssignmentOffer.created_at.desc())
            )
        ).all()
    )


@router.get("/{offer_id}", response_model=OfferView)
async def get_offer(
    offer_id: uuid.UUID, principal: Principal, session: DbSession
) -> AssignmentOffer:
    offer = await session.get(AssignmentOffer, offer_id)
    if offer is None or offer.recipient_user_id != principal.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found")
    return offer


@router.post("/{offer_id}/accept", response_model=OfferView)
async def accept_offer(
    offer_id: uuid.UUID,
    body: OfferDecisionRequest,
    principal: Principal,
    session: DbSession,
    request: Request,
    idempotency_key: IdempotencyKey,
) -> AssignmentOffer:
    try:
        return await decide_offer(
            session,
            offer_id=offer_id,
            principal=principal,
            accept=True,
            correlation_id=request.state.correlation_id,
            idempotency_key=idempotency_key,
        )
    except OfferError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/{offer_id}/decline", response_model=OfferView)
async def decline_offer(
    offer_id: uuid.UUID,
    body: OfferDecisionRequest,
    principal: Principal,
    session: DbSession,
    request: Request,
    idempotency_key: IdempotencyKey,
) -> AssignmentOffer:
    try:
        return await decide_offer(
            session,
            offer_id=offer_id,
            principal=principal,
            accept=False,
            correlation_id=request.state.correlation_id,
            idempotency_key=idempotency_key,
        )
    except OfferError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
