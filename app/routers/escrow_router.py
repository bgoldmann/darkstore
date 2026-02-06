# Escrow actions: open dispute (US-020).
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import require_user
from app.database import get_db
from app.models.order import Order, EscrowStatus
from app.models.user import User
from app.templating import templates

router = APIRouter()


async def _order_buyer_or_seller(db: AsyncSession, ref: str, user: User) -> Order | None:
    result = await db.execute(
        select(Order)
        .where(Order.ref == ref)
        .where((Order.user_id == user.id) | (Order.primary_seller_id == user.id))
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()


@router.get("/orders/{ref}/dispute", response_class=HTMLResponse)
async def dispute_page(
    request: Request,
    ref: str,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    order = await _order_buyer_or_seller(db, ref, user)
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    escrow_status = order.escrow_status or EscrowStatus.NONE.value
    if escrow_status == EscrowStatus.DISPUTED.value:
        return RedirectResponse(url=f"/orders/{ref}", status_code=302)
    past_auto_finalize = (
        order.auto_finalize_at and datetime.now(timezone.utc).isoformat() > order.auto_finalize_at
    )
    if past_auto_finalize or escrow_status not in (
        EscrowStatus.AWAITING_PAYMENT.value,
        EscrowStatus.IN_ESCROW.value,
    ):
        return RedirectResponse(url=f"/orders/{ref}", status_code=302)
    has_pgp = bool(user.pgp_public_key and user.pgp_public_key.strip())
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        "escrow/dispute.html",
        {
            "request": request,
            "user": user,
            "order": order,
            "has_pgp": has_pgp,
            "error": error,
        },
    )


@router.post("/orders/{ref}/dispute")
async def dispute_open(
    ref: str,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    order = await _order_buyer_or_seller(db, ref, user)
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    if not (user.pgp_public_key and user.pgp_public_key.strip()):
        return RedirectResponse(
            url=f"/orders/{ref}/dispute?error=pgp_required",
            status_code=302,
        )
    escrow_status = order.escrow_status or EscrowStatus.NONE.value
    if escrow_status == EscrowStatus.DISPUTED.value:
        return RedirectResponse(url=f"/orders/{ref}", status_code=302)
    past_auto_finalize = (
        order.auto_finalize_at and datetime.now(timezone.utc).isoformat() > order.auto_finalize_at
    )
    if past_auto_finalize or escrow_status not in (
        EscrowStatus.AWAITING_PAYMENT.value,
        EscrowStatus.IN_ESCROW.value,
    ):
        return RedirectResponse(url=f"/orders/{ref}", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    order.escrow_status = EscrowStatus.DISPUTED.value
    order.dispute_opened_at = now
    order.updated_at = now
    return RedirectResponse(url=f"/orders/{ref}", status_code=302)
