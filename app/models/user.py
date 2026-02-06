# User and role model (US-006 least privilege).
from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.cart import Cart
    from app.models.order import Order


def _uuid7_hex() -> str:
    return uuid.uuid4().hex[:16]


class UserRole(str, PyEnum):
    BUYER = "buyer"
    SELLER = "seller"
    SUPPORT = "support"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, default=_uuid7_hex)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    passphrase_hash: Mapped[str] = mapped_column(String(255))
    totp_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.BUYER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String(50))  # ISO timestamp

    products: Mapped[list[Product]] = relationship("Product", back_populates="seller")
    cart: Mapped["Cart | None"] = relationship("Cart", back_populates="user", uselist=False)
    orders: Mapped[list[Order]] = relationship("Order", back_populates="user")

    def has_role(self, *roles: UserRole) -> bool:
        return self.role in roles

    def can_manage_orders(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPPORT)

    def can_manage_products(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SELLER)

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
