"""
Custom exception classes for the resume job matching system.
Provides structured error handling with proper HTTP status codes and error messages.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """Base exception class for custom application exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class FileProcessingError(BaseCustomException):
    """Exception raised when file processing fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details={**(details or {}), "file_path": file_path},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class DocumentExtractionError(BaseCustomException):
    """Exception raised when document text extraction fails."""
    
    def __init__(self, message: str, file_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DOCUMENT_EXTRACTION_ERROR",
            details={**(details or {}), "file_type": file_type},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class EmbeddingGenerationError(BaseCustomException):
    """Exception raised when embedding generation fails."""
    
    def __init__(self, message: str, text_length: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EMBEDDING_GENERATION_ERROR",
            details={**(details or {}), "text_length": text_length},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class MatchingEngineError(BaseCustomException):
    """Exception raised when matching engine operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MATCHING_ENGINE_ERROR",
            details={**(details or {}), "operation": operation},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ExplanationServiceError(BaseCustomException):
    """Exception raised when explanation generation fails."""
    
    def __init__(self, message: str, service_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXPLANATION_SERVICE_ERROR",
            details={**(details or {}), "service_type": service_type},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class DatabaseError(BaseCustomException):
    """Exception raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={**(details or {}), "operation": operation},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ValidationError(BaseCustomException):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={**(details or {}), "field": field},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class AuthenticationError(BaseCustomException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(BaseCustomException):
    """Exception raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundError(BaseCustomException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=status.HTTP_404_NOT_FOUND
        )


class RateLimitError(BaseCustomException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class ExternalServiceError(BaseCustomException):
    """Exception raised when external service calls fail."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={**(details or {}), "service_name": service_name},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ConfigurationError(BaseCustomException):
    """Exception raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={**(details or {}), "config_key": config_key},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_http_exception(exc: BaseCustomException) -> HTTPException:
    """Convert custom exception to FastAPI HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )