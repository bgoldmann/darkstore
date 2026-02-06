# Session, passphrase validation, 2FA, role checks (US-005, US-006, US-017).
from __future__ import annotations

import re
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from itsdangerous import BadSignature, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_passphrase(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_passphrase(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def validate_passphrase(plain: str) -> list[str]:
    """Return list of policy violation messages (US-005)."""
    err: list[str] = []
    if len(plain) < settings.passphrase_min_length:
        err.append(f"Passphrase must be at least {settings.passphrase_min_length} characters.")
    if settings.passphrase_require_upper and not re.search(r"[A-Z]", plain):
        err.append("Passphrase must contain at least one uppercase letter.")
    if settings.passphrase_require_lower and not re.search(r"[a-z]", plain):
        err.append("Passphrase must contain at least one lowercase letter.")
    if settings.passphrase_require_digit and not re.search(r"\d", plain):
        err.append("Passphrase must contain at least one digit.")
    if settings.passphrase_require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\",./<>?\\|`~]", plain):
        err.append("Passphrase must contain at least one special character.")
    return err


def make_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt="session")


def encode_session(user_id: int, role: str) -> str:
    s = make_serializer()
    return s.dumps({"user_id": user_id, "role": role}, salt="session")


def decode_session(token: str) -> dict | None:
    s = make_serializer()
    try:
        return s.loads(token, salt="session", max_age=settings.session_ttl_seconds)
    except BadSignature:
        return None


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    data = decode_session(token)
    if not data:
        return None
    result = await db.execute(select(User).where(User.id == data["user_id"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    return user


async def require_user(
    current: User | None = Depends(get_current_user),
) -> User:
    if current is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current


def require_role(*roles: UserRole):
    async def _require_role(user: User = Depends(require_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _require_role


RequireBuyer = require_role(UserRole.BUYER, UserRole.SELLER, UserRole.SUPPORT, UserRole.ADMIN)
RequireSeller = require_role(UserRole.SELLER, UserRole.ADMIN)
RequireSupport = require_role(UserRole.SUPPORT, UserRole.ADMIN)
RequireAdmin = require_role(UserRole.ADMIN)
