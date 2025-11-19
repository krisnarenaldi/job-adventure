"""
Centralized error handling with retry logic and graceful degradation.
Provides comprehensive error handling for all service operations.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
import traceback
from datetime import datetime, timedelta

from app.core.exceptions import (
    BaseCustomException, FileProcessingError, DocumentExtractionError,
    EmbeddingGenerationError, MatchingEngineError, ExplanationServiceError,
    DatabaseError, ExternalServiceError, RateLimitError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreaker:
    """Circuit breaker pattern implementation for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise ExternalServiceError(
                        f"Circuit breaker is OPEN for {func.__name__}",
                        service_name=func.__name__,
                        details={"retry_after": self.recovery_timeout}
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable[..., T],
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs
    ) -> T:
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for delay after each failure
            exceptions: Tuple of exceptions to catch and retry
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                    break
                
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        raise last_exception


class ErrorHandler:
    """Centralized error handling with logging and monitoring."""
    
    def __init__(self):
        self.retry_handler = RetryHandler()
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    async def handle_file_processing_error(
        self,
        error: Exception,
        file_path: Optional[str] = None,
        operation: str = "file_processing"
    ) -> FileProcessingError:
        """Handle file processing errors with appropriate logging."""
        error_msg = f"File processing failed: {str(error)}"
        
        await self._log_error(error, operation, {"file_path": file_path})
        
        if "permission" in str(error).lower():
            return FileProcessingError(
                "File access denied. Check file permissions.",
                file_path=file_path,
                details={"original_error": str(error)}
            )
        elif "not found" in str(error).lower():
            return FileProcessingError(
                "File not found. Please check the file path.",
                file_path=file_path,
                details={"original_error": str(error)}
            )
        elif "size" in str(error).lower():
            return FileProcessingError(
                "File size exceeds maximum allowed limit.",
                file_path=file_path,
                details={"original_error": str(error)}
            )
        else:
            return FileProcessingError(
                error_msg,
                file_path=file_path,
                details={"original_error": str(error)}
            )
    
    async def handle_document_extraction_error(
        self,
        error: Exception,
        file_type: Optional[str] = None,
        operation: str = "document_extraction"
    ) -> DocumentExtractionError:
        """Handle document extraction errors with fallback strategies."""
        error_msg = f"Document extraction failed: {str(error)}"
        
        await self._log_error(error, operation, {"file_type": file_type})
        
        if "corrupt" in str(error).lower() or "invalid" in str(error).lower():
            return DocumentExtractionError(
                "Document appears to be corrupted or invalid.",
                file_type=file_type,
                details={"original_error": str(error), "suggestion": "Try re-uploading the file"}
            )
        elif "password" in str(error).lower() or "encrypted" in str(error).lower():
            return DocumentExtractionError(
                "Document is password protected or encrypted.",
                file_type=file_type,
                details={"original_error": str(error), "suggestion": "Upload an unprotected version"}
            )
        else:
            return DocumentExtractionError(
                error_msg,
                file_type=file_type,
                details={"original_error": str(error)}
            )
    
    async def handle_ai_service_error(
        self,
        error: Exception,
        service_name: str,
        operation: str = "ai_processing"
    ) -> BaseCustomException:
        """Handle AI service errors with appropriate fallback strategies."""
        await self._log_error(error, operation, {"service_name": service_name})
        
        if "rate limit" in str(error).lower() or "quota" in str(error).lower():
            return RateLimitError(
                f"{service_name} rate limit exceeded. Please try again later.",
                retry_after=300  # 5 minutes
            )
        elif "timeout" in str(error).lower():
            return ExternalServiceError(
                f"{service_name} request timed out. Service may be overloaded.",
                service_name=service_name,
                details={"original_error": str(error), "suggestion": "Retry with smaller input"}
            )
        elif "authentication" in str(error).lower() or "api key" in str(error).lower():
            return ExternalServiceError(
                f"{service_name} authentication failed. Check API configuration.",
                service_name=service_name,
                details={"original_error": str(error)}
            )
        elif service_name.lower() == "embedding":
            return EmbeddingGenerationError(
                f"Embedding generation failed: {str(error)}",
                details={"original_error": str(error), "fallback": "Using zero vector"}
            )
        elif service_name.lower() == "explanation":
            return ExplanationServiceError(
                f"Explanation generation failed: {str(error)}",
                service_type="LLM",
                details={"original_error": str(error), "fallback": "Using template explanation"}
            )
        else:
            return ExternalServiceError(
                f"{service_name} service error: {str(error)}",
                service_name=service_name,
                details={"original_error": str(error)}
            )
    
    async def handle_database_error(
        self,
        error: Exception,
        operation: str = "database_operation"
    ) -> DatabaseError:
        """Handle database errors with connection retry logic."""
        await self._log_error(error, operation)
        
        if "connection" in str(error).lower():
            return DatabaseError(
                "Database connection failed. Please try again.",
                operation=operation,
                details={"original_error": str(error), "suggestion": "Check database connectivity"}
            )
        elif "timeout" in str(error).lower():
            return DatabaseError(
                "Database operation timed out. Query may be too complex.",
                operation=operation,
                details={"original_error": str(error), "suggestion": "Simplify query or try again"}
            )
        elif "constraint" in str(error).lower() or "unique" in str(error).lower():
            return DatabaseError(
                "Database constraint violation. Data may already exist.",
                operation=operation,
                details={"original_error": str(error)}
            )
        else:
            return DatabaseError(
                f"Database operation failed: {str(error)}",
                operation=operation,
                details={"original_error": str(error)}
            )
    
    async def _log_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log error with context and update error tracking."""
        error_key = f"{operation}:{type(error).__name__}"
        
        # Update error counts
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = datetime.utcnow()
        
        # Log with full context
        logger.error(
            f"Error in {operation}: {str(error)}",
            extra={
                "operation": operation,
                "error_type": type(error).__name__,
                "error_count": self.error_counts[error_key],
                "context": context or {},
                "traceback": traceback.format_exc()
            }
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": dict(self.error_counts),
            "last_errors": {k: v.isoformat() for k, v in self.last_errors.items()},
            "total_errors": sum(self.error_counts.values())
        }
    
    def reset_error_stats(self):
        """Reset error statistics."""
        self.error_counts.clear()
        self.last_errors.clear()


class GracefulDegradation:
    """Handles graceful degradation when services fail."""
    
    @staticmethod
    async def embedding_fallback(text: str, dimension: int = 384) -> List[float]:
        """Fallback for embedding generation using simple text features."""
        logger.info("Using embedding fallback - generating feature-based vector")
        
        # Simple text-based features
        features = []
        
        # Text length feature (normalized)
        features.append(min(len(text) / 1000.0, 1.0))
        
        # Word count feature (normalized)
        word_count = len(text.split())
        features.append(min(word_count / 500.0, 1.0))
        
        # Character diversity
        unique_chars = len(set(text.lower()))
        features.append(min(unique_chars / 26.0, 1.0))
        
        # Keyword presence (simple scoring)
        keywords = ['experience', 'skill', 'education', 'project', 'work', 'manage', 'develop']
        keyword_score = sum(1 for keyword in keywords if keyword in text.lower()) / len(keywords)
        features.append(keyword_score)
        
        # Pad or truncate to desired dimension
        while len(features) < dimension:
            features.append(0.0)
        
        return features[:dimension]
    
    @staticmethod
    def template_explanation_fallback(
        match_score: float,
        matched_skills: List[str],
        missing_skills: List[str]
    ) -> str:
        """Fallback explanation when LLM service fails."""
        logger.info("Using template explanation fallback")
        
        if match_score >= 80:
            assessment = "Excellent match"
            recommendation = "Highly recommended"
        elif match_score >= 60:
            assessment = "Good match"
            recommendation = "Recommended with minor considerations"
        elif match_score >= 40:
            assessment = "Moderate match"
            recommendation = "Consider with skill development plan"
        else:
            assessment = "Limited match"
            recommendation = "Not recommended for this role"
        
        explanation = f"""**Assessment**: {assessment} ({match_score:.1f}% compatibility)

**Strengths**:
{chr(10).join(f"• {skill}" for skill in matched_skills[:3]) if matched_skills else "• Basic qualifications present"}

**Areas for Improvement**:
{chr(10).join(f"• Missing: {skill}" for skill in missing_skills[:3]) if missing_skills else "• No significant gaps identified"}

**Recommendation**: {recommendation}

*Note: This is a simplified analysis. For detailed insights, please try again when our AI services are available.*"""
        
        return explanation
    
    @staticmethod
    def simple_skill_matching_fallback(
        job_text: str,
        resume_text: str
    ) -> Dict[str, Any]:
        """Fallback skill matching using keyword analysis."""
        logger.info("Using simple skill matching fallback")
        
        # Common skills to look for
        common_skills = [
            'python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask',
            'machine learning', 'data science', 'analytics', 'statistics',
            'project management', 'agile', 'scrum', 'leadership', 'communication'
        ]
        
        job_lower = job_text.lower()
        resume_lower = resume_text.lower()
        
        job_skills = [skill for skill in common_skills if skill in job_lower]
        resume_skills = [skill for skill in common_skills if skill in resume_lower]
        
        matched_skills = list(set(job_skills) & set(resume_skills))
        missing_skills = list(set(job_skills) - set(resume_skills))
        
        # Simple similarity based on word overlap
        job_words = set(job_lower.split())
        resume_words = set(resume_lower.split())
        
        common_words = job_words & resume_words
        total_words = job_words | resume_words
        
        similarity_score = len(common_words) / len(total_words) if total_words else 0.0
        match_score = similarity_score * 100
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_score': match_score,
            'similarity_score': similarity_score,
            'fallback_used': True
        }


# Global error handler instance
error_handler = ErrorHandler()

# Circuit breakers for external services
embedding_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60,
    expected_exception=(EmbeddingGenerationError, ExternalServiceError)
)

explanation_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=120,
    expected_exception=(ExplanationServiceError, ExternalServiceError, RateLimitError)
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=DatabaseError
)