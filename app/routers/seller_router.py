# Seller product listing and management (US-019).
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RequireSeller, get_current_user, require_user
from app.database import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.templating import templates

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def seller_dashboard(
    request: Request,
    user: User = Depends(RequireSeller),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if user.role.value == "admin":
        result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    else:
        result = await db.execute(select(Product).where(Product.seller_id == user.id).order_by(Product.created_at.desc()))
    products = result.scalars().all()
    # Orders where this seller is primary (for escrow/release)
    order_result = await db.execute(
        select(Order).where(Order.primary_seller_id == user.id).order_by(Order.created_at.desc())
    )
    seller_orders = order_result.scalars().all()
    return templates.TemplateResponse(
        "seller/dashboard.html",
        {"request": request, "user": user, "products": products, "seller_orders": seller_orders},
    )


@router.get("/new", response_class=HTMLResponse)
async def product_new_page(request: Request, user: User = Depends(RequireSeller)):
    return templates.TemplateResponse("seller/product_form.html", {"request": request, "user": user, "product": None})


@router.post("/new")
async def product_create(
    request: Request,
    user: User = Depends(RequireSeller),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    form = await request.form()
    title = (form.get("title") or "").strip()
    description = (form.get("description") or "").strip()
    try:
        price_cents = int(float(form.get("price", 0)) * 100)
    except (ValueError, TypeError):
        price_cents = 0
    category = (form.get("category") or "general").strip()[:32]
    if not title or price_cents < 0:
        return templates.TemplateResponse(
            "seller/product_form.html",
            {"request": request, "user": user, "product": None, "error": "Title and price required."},
        )
    now = datetime.now(timezone.utc).isoformat()
    product = Product(
        title=title,
        description=description or None,
        price_cents=price_cents,
        category=category,
        seller_id=user.id,
        created_at=now,
    )
    db.add(product)
    await db.flush()
    return RedirectResponse(url="/seller", status_code=302)


@router.get("/edit/{slug}", response_class=HTMLResponse)
async def product_edit_page(
    request: Request,
    slug: str,
    user: User = Depends(RequireSeller),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Product).where(Product.slug == slug))
    product = result.scalar_one_or_none()
    if not product or (user.role.value != "admin" and product.seller_id != user.id):
        return PlainTextResponse("Not found", status_code=404)
    return templates.TemplateResponse("seller/product_form.html", {"request": request, "user": user, "product": product})


@router.post("/edit/{slug}")
async def product_update(
    request: Request,
    slug: str,
    user: User = Depends(RequireSeller),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Product).where(Product.slug == slug))
    product = result.scalar_one_or_none()
    if not product or (user.role.value != "admin" and product.seller_id != user.id):
        return PlainTextResponse("Not found", status_code=404)
    form = await request.form()
    product.title = (form.get("title") or product.title).strip()[:256]
    product.description = (form.get("description") or "").strip() or None
    try:
        product.price_cents = int(float(form.get("price", product.price_cents / 100)) * 100)
    except (ValueError, TypeError):
        pass
    product.category = (form.get("category") or product.category).strip()[:32]
    product.is_listed = form.get("listed") == "1"
    return RedirectResponse(url="/seller", status_code=302)


@router.post("/delist/{slug}")
async def product_delist(
    slug: str,
    user: User = Depends(RequireSeller),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(Product).where(Product.slug == slug))
    product = result.scalar_one_or_none()
    if not product or (user.role.value != "admin" and product.seller_id != user.id):
        return PlainTextResponse("Not found", status_code=404)
    product.is_listed = False
    return RedirectResponse(url="/seller", status_code=302)
