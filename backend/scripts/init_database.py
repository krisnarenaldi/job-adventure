#!/usr/bin/env python3
"""
Script to initialize the database with tables and extensions
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.database import init_db, close_db
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize the database"""
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        
        # Initialize database tables
        await init_db()
        logger.info("✅ Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    finally:
        # Close database connections
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())