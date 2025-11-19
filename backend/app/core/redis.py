"""
Redis connection and configuration
"""
import json
import pickle
from typing import Any, Optional, Union
import redis.asyncio as redis
from redis.asyncio import Redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
    
    async def connect(self) -> Redis:
        """Create Redis connection"""
        try:
            if not self.redis_client:
                # Build a safe Redis URL. settings.REDIS_URL may be None or
                # contain invalid parts (e.g. port set to 'None' from env). In
                # that case, construct the URL from host/port/db with sane
                # defaults and coercions.
                redis_url = None
                try:
                    raw_url = settings.REDIS_URL
                    if raw_url and isinstance(raw_url, str) and 'None' not in raw_url:
                        redis_url = raw_url
                    else:
                        # Coerce host/port/db to safe values
                        host = settings.REDIS_HOST or 'localhost'
                        try:
                            port = int(settings.REDIS_PORT)
                        except Exception:
                            port = 6379
                        try:
                            db = int(settings.REDIS_DB)
                        except Exception:
                            db = 0

                        redis_url = f"redis://{host}:{port}/{db}"

                except Exception:
                    # Fallback to defaults if settings are malformed
                    redis_url = "redis://localhost:6379/0"

                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=False,  # We'll handle encoding manually
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30,
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established successfully")
            return self.redis_client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Redis connection closed")
    
    async def get_client(self) -> Redis:
        """Get Redis client, create connection if needed"""
        if not self.redis_client:
            await self.connect()
        return self.redis_client


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> Redis:
    """Dependency to get Redis client"""
    return await redis_manager.get_client()