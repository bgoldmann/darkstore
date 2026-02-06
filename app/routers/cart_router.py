# Cart: add, remove, update, view (US-009).
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, require_user
from app.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.templating import templates

router = APIRouter()


async def get_or_create_cart(db: AsyncSession, user: User) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user.id))
    cart = result.scalar_one_or_none()
    if not cart:
        now = datetime.now(timezone.utc).isoformat()
        cart = Cart(user_id=user.id, updated_at=now)
        db.add(cart)
        await db.flush()
    return cart


@router.get("/cart", response_class=HTMLResponse)
async def cart_view(
    request: Request,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    cart = await get_or_create_cart(db, user)
    result = await db.execute(select(Cart).where(Cart.id == cart.id).options(selectinload(Cart.items).selectinload(CartItem.product)))
    cart = result.scalar_one()
    total_cents = sum(i.quantity * i.product.price_cents for i in cart.items)
    return templates.TemplateResponse(
        "cart/view.html",
        {"request": request, "user": user, "cart": cart, "total_cents": total_cents},
    )


@router.post("/cart/add")
async def cart_add(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(1),
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    cart = await get_or_create_cart(db, user)
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_listed))
    product = result.scalar_one_or_none()
    if not product:
        return RedirectResponse(url="/catalog", status_code=302)
    existing = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id))
    item = existing.scalar_one_or_none()
    if item:
        item.quantity += max(1, quantity)
    else:
        cart.items.append(CartItem(product_id=product_id, quantity=max(1, quantity)))
    cart.updated_at = datetime.now(timezone.utc).isoformat()
    await db.flush()
    return RedirectResponse(url="/cart", status_code=302)


@router.post("/cart/remove")
async def cart_remove(
    request: Request,
    item_id: int = Form(...),
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(CartItem).join(Cart).where(Cart.user_id == user.id, CartItem.id == item_id))
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
    return RedirectResponse(url="/cart", status_code=302)


@router.post("/cart/update")
async def cart_update(
    request: Request,
    item_id: int = Form(...),
    quantity: int = Form(...),
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(CartItem).join(Cart).where(Cart.user_id == user.id, CartItem.id == item_id))
    item = result.scalar_one_or_none()
    if item:
        item.quantity = max(0, quantity)
        if item.quantity == 0:
            await db.delete(item)
    return RedirectResponse(url="/cart", status_code=302)
