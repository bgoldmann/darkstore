# Order list and detail for buyers (US-011).
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import require_user
from app.database import get_db
from app.models.order import Order, OrderItem
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


@router.get("/orders/{ref}", response_class=HTMLResponse)
async def order_detail(
    request: Request,
    ref: str,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(Order).where(Order.ref == ref, Order.user_id == user.id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        return PlainTextResponse("Not found", status_code=404)
    total_cents = sum(i.quantity * i.price_cents for i in order.items)
    return templates.TemplateResponse(
        "orders/detail.html",
        {"request": request, "user": user, "order": order, "total_cents": total_cents},
    )
