#!/usr/bin/env python3
"""
Script to enable pgvector extension in Neon database
"""
import asyncio
import asyncpg
from app.core.config import settings

async def enable_pgvector():
    """Enable pgvector extension in the database"""
    try:
        # Connect to the database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector extension enabled successfully")
        
        # Verify the extension is installed
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');"
        )
        
        if result:
            print("✅ pgvector extension is active")
        else:
            print("❌ pgvector extension is not active")
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error enabling pgvector extension: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(enable_pgvector())