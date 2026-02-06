# Catalog and product listing (US-008); relative links, no PII in URLs.
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.product import Product
from app.templating import templates
from fastapi import Depends
from typing import Annotated

router = APIRouter()


@router.get("/catalog", response_class=HTMLResponse)
async def catalog_list(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
    page: int = 1,
    size: int = 20,
):
    q = select(Product).where(Product.is_listed).order_by(Product.created_at.desc())
    if category:
        q = q.where(Product.category == category)
    q = q.offset((page - 1) * size).limit(size)
    result = await db.execute(q)
    products = result.scalars().all()
    return templates.TemplateResponse(
        "catalog/list.html",
        {"request": request, "user": getattr(request.state, "user", None), "products": products, "category": category, "page": page},
    )


@router.get("/p/{slug}", response_class=HTMLResponse)
async def product_detail(
    request: Request,
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Product).where(Product.slug == slug, Product.is_listed))
    product = result.scalar_one_or_none()
    if not product:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("Not found", status_code=404)
    return templates.TemplateResponse("catalog/detail.html", {"request": request, "user": getattr(request.state, "user", None), "product": product})
