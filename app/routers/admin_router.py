# Admin: order management (US-011).
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import RequireAdmin, RequireSupport
from app.database import get_db
from app.models.order import Order, OrderStatus
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
    total_cents = sum(i.quantity * i.price_cents for i in order.items)
    return templates.TemplateResponse(
        "admin/order_detail.html",
        {"request": request, "user": user, "order": order, "total_cents": total_cents},
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
    from datetime import datetime, timezone
    order.updated_at = datetime.now(timezone.utc).isoformat()
    return RedirectResponse(url=f"/admin/orders/{ref}", status_code=302)
