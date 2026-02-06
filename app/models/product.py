# Product and category (US-008, US-019); no PII in URLs.
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.cart import CartItem
    from app.models.order import OrderItem


def _slug_id() -> str:
    return uuid.uuid4().hex[:12]


class ProductCategory(str, __import__("enum").Enum):
    GENERAL = "general"
    ELECTRONICS = "electronics"
    BOOKS = "books"
    OTHER = "other"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(16), unique=True, index=True, default=_slug_id)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(32), default="general")
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_listed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String(50))

    seller: Mapped[User] = relationship("User", back_populates="products")
    order_items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="product")

    @property
    def price_display(self) -> str:
        return f"{self.price_cents / 100:.2f}"
