# Order list and detail for buyers (US-011); escrow actions (US-020).
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
from app.models.order import Order, OrderItem, EscrowStatus
from app.models.user import User
from app.templating import templates

router = APIRouter()


@router.get("/orders", response_class=HTMLResponse)
async def order_list(
    request: Request,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return templates.TemplateResponse("orders/list.html", {"request": request, "user": user, "orders": orders})


async def _order_for_user_ref(db: AsyncSession, ref: str, user: User) -> Order | None:
    """Load order by ref if user is buyer or primary seller."""
    result = await db.execute(
        select(Order)
        .where(Order.ref == ref)
        .where((Order.user_id == user.id) | (Order.primary_seller_id == user.id))
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()


@router.get("/orders/{ref}", response_class=HTMLResponse)
async def order_detail(
    request: Request,
    ref: str,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    order = await _order_for_user_ref(db, ref, user)
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    total_cents = order.escrow_amount_cents or sum(i.quantity * i.price_cents for i in order.items)
    is_buyer = order.user_id == user.id
    is_seller = order.primary_seller_id == user.id
    escrow_status = order.escrow_status or EscrowStatus.NONE.value
    can_report_payment = is_buyer and escrow_status == EscrowStatus.AWAITING_PAYMENT.value
    can_confirm_release = is_buyer and escrow_status == EscrowStatus.IN_ESCROW.value
    past_auto_finalize = (
        order.auto_finalize_at and datetime.now(timezone.utc).isoformat() > order.auto_finalize_at
    )
    can_open_dispute = (is_buyer or is_seller) and escrow_status in (
        EscrowStatus.AWAITING_PAYMENT.value,
        EscrowStatus.IN_ESCROW.value,
    ) and not past_auto_finalize and escrow_status != EscrowStatus.DISPUTED.value
    return templates.TemplateResponse(
        "orders/detail.html",
        {
            "request": request,
            "user": user,
            "order": order,
            "total_cents": total_cents,
            "is_buyer": is_buyer,
            "is_seller": is_seller,
            "can_report_payment": can_report_payment,
            "can_confirm_release": can_confirm_release,
            "can_open_dispute": can_open_dispute,
            "past_auto_finalize": past_auto_finalize,
        },
    )


@router.post("/orders/{ref}/report-payment")
async def order_report_payment(
    ref: str,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    order = await _order_for_user_ref(db, ref, user)
    if not order or order.user_id != user.id:
        return PlainTextResponse("Not found", status_code=404)
    if (order.escrow_status or EscrowStatus.NONE.value) != EscrowStatus.AWAITING_PAYMENT.value:
        return RedirectResponse(url=f"/orders/{ref}", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    order.buyer_reported_payment_at = now
    order.updated_at = now
    return RedirectResponse(url=f"/orders/{ref}", status_code=302)


@router.post("/orders/{ref}/confirm-release")
async def order_confirm_release(
    ref: str,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    order = await _order_for_user_ref(db, ref, user)
    if not order or order.user_id != user.id:
        return PlainTextResponse("Not found", status_code=404)
    if (order.escrow_status or EscrowStatus.NONE.value) != EscrowStatus.IN_ESCROW.value:
        return RedirectResponse(url=f"/orders/{ref}", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    order.escrow_status = EscrowStatus.RELEASED_TO_SELLER.value
    order.updated_at = now
    return RedirectResponse(url=f"/orders/{ref}", status_code=302)
