"""
API response caching middleware using Redis
"""
import json
import hashlib
from typing import Dict, Any, Optional, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """Redis-based API response caching middleware"""
    
    def __init__(
        self, 
        app,
        cache_ttl: int = 900,  # 15 minutes default
        cacheable_methods: List[str] = None,
        cacheable_paths: List[str] = None,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_methods = cacheable_methods or ["GET"]
        self.cacheable_paths = cacheable_paths or []
        self.exclude_paths = exclude_paths or [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/openapi.json"
        ]
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached"""
        
        # Check method
        if request.method not in self.cacheable_methods:
            return False
        
        # Check excluded paths
        path = request.url.path
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # If specific cacheable paths are defined, check them
        if self.cacheable_paths:
            for cacheable_path in self.cacheable_paths:
                if path.startswith(cacheable_path):
                    return True
            return False
        
        # Default: cache API endpoints
        return path.startswith("/api/v1/")
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        
        # Include path, query parameters, and relevant headers
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        
        # Include user-specific data if available
        if hasattr(request.state, 'current_user') and request.state.current_user:
            key_components.append(str(request.state.current_user.id))
        
        # Create hash of components
        key_string = "|".join(key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with caching"""
        
        # Check if request should be cached
        if not self._should_cache_request(request):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        endpoint = request.url.path
        
        # Try to get cached response
        try:
            cached_response = await cache_service.get_cached_api_response(endpoint, cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint}")
                
                # Return cached response
                return JSONResponse(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers={"X-Cache": "HIT"}
                )
        except Exception as e:
            logger.warning(f"Failed to get cached response: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if (
            response.status_code == 200 and 
            isinstance(response, JSONResponse) and
            hasattr(response, 'body')
        ):
            try:
                # Extract response content
                response_content = json.loads(response.body.decode())
                
                cache_data = {
                    "content": response_content,
                    "status_code": response.status_code,
                }
                
                # Cache the response
                await cache_service.cache_api_response(
                    endpoint, 
                    cache_key, 
                    cache_data, 
                    expire_minutes=self.cache_ttl // 60
                )
                
                logger.debug(f"Cached response for {endpoint}")
                
                # Add cache header
                response.headers["X-Cache"] = "MISS"
                
            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")
        
        return response


class CacheControl:
    """Utility class for cache control decorators and functions"""
    
    @staticmethod
    def no_cache(request: Request):
        """Mark request as non-cacheable"""
        request.state.no_cache = True
    
    @staticmethod
    def cache_for(request: Request, minutes: int):
        """Set custom cache duration for request"""
        request.state.cache_ttl = minutes * 60
    
    @staticmethod
    async def invalidate_cache_pattern(pattern: str) -> int:
        """Invalidate all cached responses matching pattern"""
        try:
            return await cache_service.clear_pattern(f"api_response:*{pattern}*")
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
            return 0
    
    @staticmethod
    async def invalidate_user_cache(user_id: str) -> int:
        """Invalidate all cached responses for a specific user"""
        try:
            return await cache_service.clear_pattern(f"api_response:*{user_id}*")
        except Exception as e:
            logger.error(f"Failed to invalidate user cache {user_id}: {e}")
            return 0


# Cache control decorators
def cache_response(ttl_minutes: int = 15):
    """Decorator to enable caching for specific endpoints"""
    def decorator(func):
        func._cache_enabled = True
        func._cache_ttl = ttl_minutes * 60
        return func
    return decorator


def no_cache(func):
    """Decorator to disable caching for specific endpoints"""
    func._no_cache = True
    return func