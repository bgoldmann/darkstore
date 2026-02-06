# Auth: register, login, logout, 2FA (US-005, US-017).
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

import pyotp
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    encode_session,
    get_current_user,
    hash_passphrase,
    require_user,
    validate_passphrase,
    verify_passphrase,
)
from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole
from app.templating import templates

settings = get_settings()
router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request, "user": getattr(request.state, "user", None)})


@router.post("/login")
async def login(
    request: Request,
    username: Annotated[str, Form()],
    passphrase: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_passphrase(passphrase, user.passphrase_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "user": None, "error": "Invalid username or passphrase."},
        )
    # TODO: if user.totp_enabled, require TOTP code here
    token = encode_session(user.id, user.role.value)
    r = RedirectResponse(url="/", status_code=302)
    r.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        samesite=settings.session_same_site,
        secure=settings.session_secure,
    )
    return r


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "user": getattr(request.state, "user", None), "min_length": settings.passphrase_min_length},
    )


@router.post("/register")
async def register(
    request: Request,
    username: Annotated[str, Form()],
    passphrase: Annotated[str, Form()],
    passphrase_confirm: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if passphrase != passphrase_confirm:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "user": None, "error": "Passphrases do not match.", "min_length": settings.passphrase_min_length},
        )
    err = validate_passphrase(passphrase)
    if err:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "user": None, "errors": err, "min_length": settings.passphrase_min_length},
        )
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "user": None, "error": "Username already taken.", "min_length": settings.passphrase_min_length},
        )
    now = datetime.now(timezone.utc).isoformat()
    user = User(
        username=username,
        passphrase_hash=hash_passphrase(passphrase),
        role=UserRole.BUYER,
        created_at=now,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    token = encode_session(user.id, user.role.value)
    r = RedirectResponse(url="/", status_code=302)
    r.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        samesite=settings.session_same_site,
        secure=settings.session_secure,
    )
    return r


@router.get("/logout")
async def logout(request: Request):
    r = RedirectResponse(url="/", status_code=302)
    r.delete_cookie(settings.session_cookie_name)
    return r
