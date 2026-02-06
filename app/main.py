# Darkstore FastAPI app – Tor onion store (US-001, US-002, US-003, US-017).
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.auth import decode_session
from app.config import get_settings
from app.database import async_session_factory, init_db
from app.models.user import User
from app.routers import auth_router, catalog_router, cart_router, checkout_router, orders_router, seller_router, admin_router, policy_router, escrow_router

settings = get_settings()

# Minimal logging: no passphrases or payment data (US-003).
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
if settings.log_path:
    fh = logging.FileHandler(settings.log_path)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    logging.getLogger().addHandler(fh)
logger = logging.getLogger("darkstore")


# Strip server/application headers (US-002).
HEADERS_TO_REMOVE = {
    "server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version",
    "x-runtime", "x-version", "x-frame-options", "x-content-type-options",
}
# We set minimal safe headers only; no version info.
SAFE_HEADERS = {"x-content-type-options": "nosniff"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # shutdown if needed


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=None if not settings.debug else "/docs",
    redoc_url=None if not settings.debug else "/redoc",
)


@app.middleware("http")
async def add_user_and_strip_headers(request: Request, call_next):
    request.state.user = None
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        data = decode_session(token)
        if data:
            async with async_session_factory() as db:
                result = await db.execute(select(User).where(User.id == data["user_id"]))
                user = result.scalar_one_or_none()
                if user and user.is_active:
                    request.state.user = user
    response = await call_next(request)
    for h in HEADERS_TO_REMOVE:
        response.headers.pop(h, None)
    for k, v in SAFE_HEADERS.items():
        response.headers[k] = v
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


# Static (relative links only for onion; no mixed content).
from app.templating import BASE_DIR

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Include routers
app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(catalog_router, prefix="", tags=["catalog"])
app.include_router(cart_router, prefix="", tags=["cart"])
app.include_router(checkout_router, prefix="", tags=["checkout"])
app.include_router(orders_router, prefix="", tags=["orders"])
app.include_router(seller_router, prefix="/seller", tags=["seller"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(policy_router, prefix="", tags=["policy"])
app.include_router(escrow_router, prefix="", tags=["escrow"])
app.include_router(profile_router, prefix="", tags=["profile"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from app.templating import templates
    return templates.TemplateResponse("home.html", {"request": request, "user": getattr(request.state, "user", None)})
