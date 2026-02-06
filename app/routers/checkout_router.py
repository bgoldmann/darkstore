# Checkout flow (US-009, US-020 escrow).
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import require_user
from app.config import get_settings
from app.database import get_db
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus, EscrowStatus
from app.models.product import Product
from app.models.user import User
from app.templating import templates

router = APIRouter()


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(
    request: Request,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Cart).where(Cart.user_id == user.id).options(selectinload(Cart.items).selectinload(CartItem.product)))
    cart = result.scalar_one_or_none()
    if not cart or not cart.items:
        return RedirectResponse(url="/catalog", status_code=302)
    total_cents = sum(i.quantity * i.product.price_cents for i in cart.items)
    return templates.TemplateResponse(
        "checkout/checkout.html",
        {"request": request, "user": user, "cart": cart, "total_cents": total_cents},
    )


@router.post("/checkout")
async def checkout_submit(
    request: Request,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    form = await request.form()
    payment_method = form.get("payment_method", "xmr") or "xmr"
    result = await db.execute(select(Cart).where(Cart.user_id == user.id).options(selectinload(Cart.items).selectinload(CartItem.product)))
    cart = result.scalar_one_or_none()
    if not cart or not cart.items:
        return RedirectResponse(url="/catalog", status_code=302)
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    settings = get_settings()
    auto_finalize_at = (now_dt + timedelta(days=settings.escrow_auto_finalize_days)).isoformat()
    primary_seller_id = cart.items[0].product.seller_id if cart.items else None
    order = Order(
        user_id=user.id,
        status=OrderStatus.PENDING.value,
        payment_method=payment_method or "xmr",
        created_at=now,
        updated_at=now,
        escrow_status=EscrowStatus.AWAITING_PAYMENT.value,
        escrow_address=None,  # Phase 1: instructions via PGP or placeholder
        escrow_amount_cents=None,  # Set after we compute total_cents
        auto_finalize_at=auto_finalize_at,
        primary_seller_id=primary_seller_id,
    )
    db.add(order)
    await db.flush()
    total_cents = 0
    for ci in cart.items:
        oi = OrderItem(
            order_id=order.id,
            product_id=ci.product_id,
            product_title=ci.product.title,
            quantity=ci.quantity,
            price_cents=ci.product.price_cents,
        )
        db.add(oi)
        total_cents += ci.quantity * ci.product.price_cents
    order.escrow_amount_cents = total_cents
    for ci in cart.items:
        await db.delete(ci)
    cart.updated_at = now
    return RedirectResponse(url=f"/orders/{order.ref}", status_code=302)
