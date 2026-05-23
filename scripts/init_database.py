#!/usr/bin/env python3
"""
Bharat Market Intelligence Agent — Database Initialization Script

Creates all tables from SQLAlchemy models and seeds initial data.
Run once to bootstrap the database, or on deployment.

Usage:
    python scripts/init_database.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings
from app.db.session import engine, init_db, close_db
from app.utils.helpers import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging("INFO")
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("Bharat Market Intelligence — Database Initialization")
    logger.info("Database: %s", settings.database_url.split("@")[-1])
    logger.info("=" * 60)

    # Step 1: Create tables
    logger.info("Step 1: Creating database tables from SQLAlchemy models...")
    try:
        from app.db.models import Base
        from sqlalchemy.ext.asyncio import create_async_engine

        async_engine = create_async_engine(settings.database_url, echo=False)
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await async_engine.dispose()
        logger.info("✅ All tables created successfully")
    except Exception as e:
        logger.error("❌ Table creation failed: %s", str(e))
        logger.error("Make sure PostgreSQL is running and pgvector extension is installed")
        return

    # Step 2: Seed companies
    logger.info("Step 2: Seeding Nifty 500 companies...")
    try:
        from scripts.seed_database import seed_companies
        count = await seed_companies()
        logger.info("✅ Seeded %d companies", count)
    except Exception as e:
        logger.error("⚠️ Company seeding failed (non-fatal): %s", str(e))

    # Step 3: Run pgvector extension setup
    logger.info("Step 3: Ensuring pgvector extension...")
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        async_engine = create_async_engine(settings.database_url, echo=False)
        async with async_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await async_engine.dispose()
        logger.info("✅ pgvector extension ready")
    except Exception as e:
        logger.error("⚠️ pgvector setup failed (non-fatal): %s", str(e))

    logger.info("=" * 60)
    logger.info("Database initialization complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
