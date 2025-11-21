import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import BaseCustomException, create_http_exception
from app.core.logging_config import configure_app_logging, get_logger
from app.core.redis import redis_manager
from app.middleware.logging_middleware import LoggingMiddleware, PerformanceMonitoringMiddleware
from app.middleware.session_middleware import SessionMiddleware
from app.middleware.cache_middleware import CacheMiddleware
from app.api.v1.api import api_router

# Configure logging before creating the app
configure_app_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Resume Job Matching System")
    
    # Initialize Redis connection
    try:
        await redis_manager.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # Don't fail startup, caching will be disabled
    
    # Initialize services
    try:
        from app.services.embedding_service import embedding_service
        from app.services.explanation_service import explanation_service
        from app.services.monitoring_service import monitoring_service
        
        await embedding_service.initialize()
        await explanation_service.initialize()
        await monitoring_service.start_monitoring()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't fail startup, services will handle graceful degradation
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Job Matching System")
    
    try:
        await embedding_service.close()
        await explanation_service.close()
        await monitoring_service.stop_monitoring()
        await redis_manager.disconnect()
        logger.info("All services closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered resume and job description matching system",
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    # allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$|https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Allow-Headers",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["Content-Disposition"],
    max_age=600,  # Cache preflight response for 10 minutes
)

# Add middleware (order matters - last added is executed first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=5.0)
app.add_middleware(SessionMiddleware, max_age=86400)  # 24 hours
app.add_middleware(
    CacheMiddleware, 
    cache_ttl=900,  # 15 minutes
    cacheable_paths=["/api/v1/analytics", "/api/v1/jobs", "/api/v1/resumes"]
)


# Global exception handlers
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """Handle custom application exceptions."""
    logger.error(
        f"Custom exception in {request.method} {request.url}: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(
        f"Validation error in {request.method} {request.url}: {exc.errors()}",
        extra={
            "validation_errors": exc.errors(),
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "message": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": {"validation_errors": exc.errors()}
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        f"HTTP exception in {request.method} {request.url}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "error_code": "HTTP_ERROR",
            "details": {}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error in {request.method} {request.url}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": {}
        }
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "resume-job-matching"}