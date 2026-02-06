# Escrow & Dispute Policy page (US-020); platform PGP key.
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.templating import templates

router = APIRouter()


@router.get("/policy/escrow", response_class=HTMLResponse)
async def escrow_policy(request: Request):
    """Escrow & Dispute Policy: time limits, dispute flow, 2-of-3 multisig, platform PGP key."""
    settings = get_settings()
    platform_pgp_key = settings.get_platform_pgp_public_key()
    return templates.TemplateResponse(
        "policy/escrow.html",
        {
            "request": request,
            "user": getattr(request.state, "user", None),
            "platform_pgp_public_key": platform_pgp_key,
        },
    )
