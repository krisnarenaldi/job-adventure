from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine with optimized settings
# Remove sslmode and channel_binding from URL as asyncpg handles SSL differently
db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
# Remove query parameters that asyncpg doesn't support in URL
if "?" in db_url:
    db_url = db_url.split("?")[0]

engine = create_async_engine(
    db_url,
    echo=False,  # Disable SQL logging for performance
    pool_size=30,  # Increased pool size for better concurrency
    max_overflow=20,  # Allow overflow connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
    pool_timeout=30,  # Timeout for getting connection from pool
    connect_args={
        "ssl": "require",  # SSL mode for asyncpg
        "server_settings": {
            "jit": "off",  # Disable JIT for faster query planning
            "application_name": "resume_matching_app",
        },
        "command_timeout": 60,  # Query timeout
        "prepared_statement_cache_size": 100,  # Cache prepared statements
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
class Base(DeclarativeBase):
    metadata = MetaData()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models.user import User
        from app.models.job import JobDescription
        from app.models.resume import Resume
        from app.models.match_result import MatchResult
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")