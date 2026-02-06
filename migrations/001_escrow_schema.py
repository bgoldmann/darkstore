# Migration: add escrow and PGP columns (US-020).
# Run once on existing DB: cd store && python -m migrations.001_escrow_schema
# New installs: init_db() create_all will create full schema; script skips if column exists.

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.database import engine


async def add_column(conn, table: str, col: str, spec: str) -> None:
    try:
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {spec}"))
    except OperationalError as e:
        if "duplicate column name" in str(e).lower():
            return
        raise


async def run() -> None:
    async with engine.begin() as conn:
        await add_column(conn, "users", "pgp_public_key", "TEXT")
        await add_column(conn, "orders", "escrow_status", "VARCHAR(32) DEFAULT 'none'")
        await add_column(conn, "orders", "escrow_address", "VARCHAR(512)")
        await add_column(conn, "orders", "escrow_amount_cents", "INTEGER")
        await add_column(conn, "orders", "escrow_funded_at", "VARCHAR(50)")
        await add_column(conn, "orders", "buyer_reported_payment_at", "VARCHAR(50)")
        await add_column(conn, "orders", "auto_finalize_at", "VARCHAR(50)")
        await add_column(conn, "orders", "primary_seller_id", "INTEGER")
        await add_column(conn, "orders", "dispute_opened_at", "VARCHAR(50)")
        await add_column(conn, "orders", "dispute_resolved_at", "VARCHAR(50)")
        await add_column(conn, "orders", "dispute_resolution", "VARCHAR(32)")
        await add_column(conn, "orders", "dispute_evidence_encrypted", "TEXT")
    print("001_escrow_schema: done.")


if __name__ == "__main__":
    asyncio.run(run())
