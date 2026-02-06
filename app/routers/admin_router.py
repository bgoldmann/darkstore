# Admin: order management (US-011); escrow mark funded and resolve dispute (US-020).
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import RequireAdmin, RequireSupport
from app.database import get_db
from app.models.order import Order, OrderStatus, EscrowStatus
from app.models.user import User
from app.templating import templates

router = APIRouter()


@router.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    user: User = Depends(RequireSupport),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(Order).order_by(Order.created_at.desc()).options(selectinload(Order.items))
    )
    orders = result.scalars().all()
    return templates.TemplateResponse("admin/orders.html", {"request": request, "user": user, "orders": orders})


@router.get("/orders/{ref}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request,
    ref: str,
    user: User = Depends(RequireSupport),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(Order).where(Order.ref == ref).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    total_cents = order.escrow_amount_cents or sum(i.quantity * i.price_cents for i in order.items)
    escrow_status = order.escrow_status or EscrowStatus.NONE.value
    can_mark_funded = escrow_status == EscrowStatus.AWAITING_PAYMENT.value
    can_resolve = user.can_resolve_escrow_dispute() and escrow_status == EscrowStatus.DISPUTED.value
    return templates.TemplateResponse(
        "admin/order_detail.html",
        {
            "request": request,
            "user": user,
            "order": order,
            "total_cents": total_cents,
            "can_mark_funded": can_mark_funded,
            "can_resolve_dispute": can_resolve,
        },
    )


@router.post("/orders/{ref}/status")
async def admin_order_status(
    ref: str,
    request: Request,
    user: User = Depends(RequireSupport),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    form = await request.form()
    status_val = form.get("status", "").strip()
    if status_val not in (s.value for s in OrderStatus):
        return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)
    result = await db.execute(select(Order).where(Order.ref == ref))
    order = result.scalar_one_or_none()
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    order.status = status_val
    order.updated_at = datetime.now(timezone.utc).isoformat()
    return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)


@router.post("/orders/{ref}/mark-funded")
async def admin_mark_funded(
    ref: str,
    user: User = Depends(RequireSupport),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if not user.can_resolve_escrow_dispute():
        return PlainTextResponse("Forbidden", status_code=403)
    result = await db.execute(select(Order).where(Order.ref == ref))
    order = result.scalar_one_or_none()
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    if (order.escrow_status or EscrowStatus.NONE.value) != EscrowStatus.AWAITING_PAYMENT.value:
        return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    order.escrow_status = EscrowStatus.IN_ESCROW.value
    order.escrow_funded_at = now
    order.updated_at = now
    return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)


@router.post("/orders/{ref}/resolve-dispute")
async def admin_resolve_dispute(
    ref: str,
    request: Request,
    user: User = Depends(RequireSupport),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if not user.can_resolve_escrow_dispute():
        return PlainTextResponse("Forbidden", status_code=403)
    form = await request.form()
    resolution = (form.get("resolution") or "").strip()
    if resolution not in ("released_to_seller", "released_to_buyer"):
        return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)
    result = await db.execute(select(Order).where(Order.ref == ref))
    order = result.scalar_one_or_none()
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    if (order.escrow_status or EscrowStatus.NONE.value) != EscrowStatus.DISPUTED.value:
        return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    order.escrow_status = resolution
    order.dispute_resolution = resolution
    order.dispute_resolved_at = now
    order.updated_at = now
    return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)
