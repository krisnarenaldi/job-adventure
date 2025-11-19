"""
Session management middleware using Redis
"""
import uuid
import json
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Redis-based session middleware"""
    
    def __init__(self, app, session_cookie: str = "session_id", max_age: int = 86400):
        super().__init__(app)
        self.session_cookie = session_cookie
        self.max_age = max_age  # 24 hours default
    
    async def dispatch(self, request: Request, call_next):
        """Process request and manage session"""
        
        # Get session ID from cookie
        session_id = request.cookies.get(self.session_cookie)
        session_data = {}
        
        if session_id:
            # Try to load existing session
            try:
                session_data = await cache_service.get_session(session_id) or {}
                if session_data:
                    logger.debug(f"Loaded session {session_id}")
                else:
                    # Session expired or doesn't exist, create new one
                    session_id = str(uuid.uuid4())
                    logger.debug(f"Session expired, created new session {session_id}")
            except Exception as e:
                logger.error(f"Failed to load session {session_id}: {e}")
                session_id = str(uuid.uuid4())
                session_data = {}
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            logger.debug(f"Created new session {session_id}")
        
        # Add session to request state
        request.state.session_id = session_id
        request.state.session = session_data
        
        # Process request
        response = await call_next(request)
        
        # Save session if it was modified
        if hasattr(request.state, 'session_modified') and request.state.session_modified:
            try:
                await cache_service.set_session(
                    session_id, 
                    request.state.session, 
                    expire_hours=self.max_age // 3600
                )
                logger.debug(f"Saved session {session_id}")
            except Exception as e:
                logger.error(f"Failed to save session {session_id}: {e}")
        
        # Set session cookie
        response.set_cookie(
            key=self.session_cookie,
            value=session_id,
            max_age=self.max_age,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response


def get_session(request: Request) -> Dict[str, Any]:
    """Get session data from request"""
    return getattr(request.state, 'session', {})


def set_session_value(request: Request, key: str, value: Any):
    """Set a value in the session"""
    if not hasattr(request.state, 'session'):
        request.state.session = {}
    
    request.state.session[key] = value
    request.state.session_modified = True


def get_session_value(request: Request, key: str, default: Any = None) -> Any:
    """Get a value from the session"""
    session = get_session(request)
    return session.get(key, default)


def clear_session(request: Request):
    """Clear all session data"""
    request.state.session = {}
    request.state.session_modified = True


async def destroy_session(request: Request):
    """Destroy the session completely"""
    session_id = getattr(request.state, 'session_id', None)
    if session_id:
        try:
            await cache_service.delete_session(session_id)
            logger.debug(f"Destroyed session {session_id}")
        except Exception as e:
            logger.error(f"Failed to destroy session {session_id}: {e}")
    
    clear_session(request)