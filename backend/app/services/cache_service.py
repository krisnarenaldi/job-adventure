"""
Redis caching service for embeddings, sessions, and API responses
"""
import json
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.redis import get_redis
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.redis_client:
            self.redis_client = await get_redis()
        return self.redis_client
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with prefix"""
        return f"{prefix}:{identifier}"
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content-based caching"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def set_cache(
        self, 
        key: str, 
        value: Any, 
        expire_seconds: Optional[int] = None,
        serialize_method: str = "json"
    ) -> bool:
        """
        Set cache value with optional expiration
        
        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: Expiration time in seconds
            serialize_method: 'json' or 'pickle'
        """
        try:
            client = await self._get_client()
            
            # Serialize value
            if serialize_method == "json":
                serialized_value = json.dumps(value, default=str)
            elif serialize_method == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                raise ValueError(f"Unsupported serialization method: {serialize_method}")
            
            # Set with expiration
            if expire_seconds:
                await client.setex(key, expire_seconds, serialized_value)
            else:
                await client.set(key, serialized_value)
            
            logger.debug(f"Cached value for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    async def get_cache(
        self, 
        key: str, 
        serialize_method: str = "json"
    ) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            key: Cache key
            serialize_method: 'json' or 'pickle'
        """
        try:
            client = await self._get_client()
            cached_value = await client.get(key)
            
            if cached_value is None:
                return None
            
            # Deserialize value
            if serialize_method == "json":
                return json.loads(cached_value)
            elif serialize_method == "pickle":
                return pickle.loads(cached_value)
            else:
                raise ValueError(f"Unsupported serialization method: {serialize_method}")
                
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete cache entry"""
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache existence for key {key}: {e}")
            return False
    
    # Embedding-specific caching methods
    async def cache_embedding(
        self, 
        text: str, 
        embedding: List[float], 
        expire_hours: int = 24
    ) -> bool:
        """Cache text embedding"""
        text_hash = self._hash_content(text)
        key = self._generate_key("embedding", text_hash)
        expire_seconds = expire_hours * 3600
        
        return await self.set_cache(
            key, 
            embedding, 
            expire_seconds, 
            serialize_method="pickle"
        )
    
    async def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        text_hash = self._hash_content(text)
        key = self._generate_key("embedding", text_hash)
        
        return await self.get_cache(key, serialize_method="pickle")
    
    # Session management methods
    async def set_session(
        self, 
        session_id: str, 
        session_data: Dict[str, Any], 
        expire_hours: int = 24
    ) -> bool:
        """Set session data"""
        key = self._generate_key("session", session_id)
        expire_seconds = expire_hours * 3600
        
        return await self.set_cache(key, session_data, expire_seconds)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = self._generate_key("session", session_id)
        return await self.get_cache(key)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        key = self._generate_key("session", session_id)
        return await self.delete_cache(key)
    
    async def extend_session(self, session_id: str, expire_hours: int = 24) -> bool:
        """Extend session expiration"""
        try:
            client = await self._get_client()
            key = self._generate_key("session", session_id)
            expire_seconds = expire_hours * 3600
            
            result = await client.expire(key, expire_seconds)
            return result
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
    
    # API response caching methods
    async def cache_api_response(
        self, 
        endpoint: str, 
        params_hash: str, 
        response_data: Any, 
        expire_minutes: int = 15
    ) -> bool:
        """Cache API response"""
        key = self._generate_key("api_response", f"{endpoint}:{params_hash}")
        expire_seconds = expire_minutes * 60
        
        return await self.set_cache(key, response_data, expire_seconds)
    
    async def get_cached_api_response(
        self, 
        endpoint: str, 
        params_hash: str
    ) -> Optional[Any]:
        """Get cached API response"""
        key = self._generate_key("api_response", f"{endpoint}:{params_hash}")
        return await self.get_cache(key)
    
    # Match result caching
    async def cache_match_results(
        self, 
        job_id: str, 
        resume_ids: List[str], 
        results: List[Dict[str, Any]], 
        expire_hours: int = 6
    ) -> bool:
        """Cache match results for a job and set of resumes"""
        resume_ids_hash = self._hash_content(",".join(sorted(resume_ids)))
        key = self._generate_key("match_results", f"{job_id}:{resume_ids_hash}")
        expire_seconds = expire_hours * 3600
        
        cache_data = {
            "job_id": job_id,
            "resume_ids": resume_ids,
            "results": results,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        return await self.set_cache(key, cache_data, expire_seconds)
    
    async def get_cached_match_results(
        self, 
        job_id: str, 
        resume_ids: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached match results"""
        resume_ids_hash = self._hash_content(",".join(sorted(resume_ids)))
        key = self._generate_key("match_results", f"{job_id}:{resume_ids_hash}")
        
        cached_data = await self.get_cache(key)
        if cached_data:
            return cached_data.get("results")
        return None
    
    # Utility methods
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            client = await self._get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            client = await self._get_client()
            info = await client.info()
            
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Global cache service instance
cache_service = CacheService()