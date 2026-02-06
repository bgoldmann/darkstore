# Orders and order items (US-011).
from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


def _order_ref() -> str:
    return uuid.uuid4().hex[:10].upper()


class EscrowStatus(str, PyEnum):
    NONE = "none"
    AWAITING_PAYMENT = "awaiting_payment"
    IN_ESCROW = "in_escrow"
    RELEASED_TO_SELLER = "released_to_seller"
    RELEASED_TO_BUYER = "released_to_buyer"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ref: Mapped[str] = mapped_column(String(16), unique=True, index=True, default=_order_ref)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.PENDING.value)
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str] = mapped_column(String(50))
    # Escrow (US-020)
    escrow_status: Mapped[str] = mapped_column(String(32), default=EscrowStatus.NONE.value)
    escrow_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    escrow_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    escrow_funded_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    buyer_reported_payment_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    auto_finalize_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primary_seller_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    dispute_opened_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dispute_resolved_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dispute_resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)  # released_to_seller | released_to_buyer
    dispute_evidence_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="orders", foreign_keys=[user_id])
    primary_seller: Mapped[User | None] = relationship("User", foreign_keys=[primary_seller_id])
    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_title: Mapped[str] = mapped_column(String(256))
    quantity: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    product: Mapped[Product] = relationship("Product", back_populates="order_items")
