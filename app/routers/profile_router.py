# Profile: PGP public key (US-020 escrow/dispute).
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user
from app.database import get_db
from app.models.user import User
from app.templating import templates

router = APIRouter()


def _looks_like_pgp_public_key(text: str) -> bool:
    """Minimal check: contains BEGIN PGP and END PGP."""
    t = (text or "").strip()
    return "BEGIN PGP" in t.upper() and "END PGP" in t.upper()


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "profile/profile.html",
        {"request": request, "user": user},
    )


@router.post("/profile")
async def profile_update(
    request: Request,
    user: User = Depends(require_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    form = await request.form()
    pgp_raw = (form.get("pgp_public_key") or "").strip()
    if pgp_raw and not _looks_like_pgp_public_key(pgp_raw):
        return templates.TemplateResponse(
            "profile/profile.html",
            {
                "request": request,
                "user": user,
                "error": "Key must be an ASCII-armored PGP public key (BEGIN PGP ... END PGP).",
            },
        )
    result = await db.execute(select(User).where(User.id == user.id))
    u = result.scalar_one_or_none()
    if u:
        u.pgp_public_key = pgp_raw or None
    return RedirectResponse(url="/profile", status_code=302)
