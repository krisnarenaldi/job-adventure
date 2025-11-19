"""
Embedding service for generating semantic embeddings using Sentence Transformers.
Handles embedding generation, caching, and batch processing.
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import asyncio
from functools import lru_cache
from app.core.config import settings
from app.core.exceptions import EmbeddingGenerationError, ExternalServiceError
from app.core.error_handler import error_handler, RetryHandler, embedding_circuit_breaker, GracefulDegradation
from app.core.logging_config import performance_logger
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing semantic embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize the embedding model."""
        try:
            # Load the sentence transformer model
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    

    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding generation."""
        if not text or not text.strip():
            return ""
        
        # Basic text cleaning
        text = text.strip()
        # Remove excessive whitespace
        text = ' '.join(text.split())
        # Truncate if too long (model has token limits)
        max_length = 8000  # Conservative limit for sentence transformers
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters for embedding")
        
        return text
    
    @embedding_circuit_breaker
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text with comprehensive error handling.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        with performance_logger.time_operation(
            "embedding_generation",
            text_length=len(text),
            model_name=self.model_name
        ):
            if not self._model:
                raise EmbeddingGenerationError(
                    "Embedding service not initialized. Call initialize() first.",
                    text_length=len(text)
                )
            
            # Preprocess text
            processed_text = self._preprocess_text(text)
            if not processed_text:
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.embedding_dimension
            
            # Check cache first
            cached_embedding = await cache_service.get_cached_embedding(processed_text)
            if cached_embedding:
                logger.debug("Retrieved embedding from cache")
                return cached_embedding
            
            try:
                # Use retry logic for embedding generation
                embedding_list = await RetryHandler.retry_with_backoff(
                    self._generate_embedding_with_fallback,
                    max_retries=2,
                    base_delay=1.0,
                    exceptions=(EmbeddingGenerationError, RuntimeError, OSError),
                    processed_text=processed_text
                )
                
                # Cache the result
                await cache_service.cache_embedding(processed_text, embedding_list)
                
                logger.debug(f"Generated embedding with dimension: {len(embedding_list)}")
                return embedding_list
                
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                
                # Use graceful degradation
                fallback_embedding = await GracefulDegradation.embedding_fallback(
                    processed_text, 
                    self.embedding_dimension
                )
                
                # Cache fallback result with shorter TTL (1 hour)
                await cache_service.cache_embedding(processed_text, fallback_embedding, expire_hours=1)
                
                return fallback_embedding
    
    async def _generate_embedding_with_fallback(self, processed_text: str) -> List[float]:
        """Generate embedding with model, includes fallback logic."""
        try:
            # Generate embedding using sentence transformer
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self._model.encode, 
                processed_text
            )
            
            # Convert numpy array to list
            return embedding.tolist()
            
        except Exception as e:
            raise await error_handler.handle_ai_service_error(
                e,
                service_name="embedding",
                operation="embedding_generation"
            )
    
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self._model:
            raise RuntimeError("Embedding service not initialized. Call initialize() first.")
        
        if not texts:
            return []
        
        # Preprocess all texts
        processed_texts = [self._preprocess_text(text) for text in texts]
        embeddings = []
        texts_to_process = []
        indices_to_process = []
        
        # Check cache for each text
        for i, processed_text in enumerate(processed_texts):
            if not processed_text:
                embeddings.append([0.0] * self.embedding_dimension)
                continue
                
            cached_embedding = await cache_service.get_cached_embedding(processed_text)
            
            if cached_embedding:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)  # Placeholder
                texts_to_process.append(processed_text)
                indices_to_process.append(i)
        
        # Process uncached texts in batch
        if texts_to_process:
            try:
                logger.info(f"Generating embeddings for {len(texts_to_process)} texts")
                
                # Run batch encoding in thread pool
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    None,
                    self._model.encode,
                    texts_to_process
                )
                
                # Process results and cache them
                for i, embedding in enumerate(batch_embeddings):
                    embedding_list = embedding.tolist()
                    original_index = indices_to_process[i]
                    embeddings[original_index] = embedding_list
                    
                    # Cache the result
                    await cache_service.cache_embedding(texts_to_process[i], embedding_list)
                
                logger.info(f"Successfully generated {len(batch_embeddings)} embeddings")
                
            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                # Fill remaining with zero vectors
                for i in indices_to_process:
                    if embeddings[i] is None:
                        embeddings[i] = [0.0] * self.embedding_dimension
        
        return embeddings
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding service."""
        stats = {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "model_loaded": self._model is not None,
        }
        
        # Get cache statistics from cache service
        try:
            cache_stats = await cache_service.get_cache_stats()
            stats["cache_stats"] = cache_stats
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
        
        return stats
    
    async def clear_cache(self) -> bool:
        """Clear all cached embeddings."""
        try:
            # Clear all embedding cache keys
            cleared_count = await cache_service.clear_pattern("embedding:*")
            logger.info(f"Cleared {cleared_count} cached embeddings")
            return True
        except Exception as e:
            logger.error(f"Failed to clear embedding cache: {e}")
            return False
    
    async def close(self):
        """Clean up resources."""
        # No resources to clean up since we use the global cache service
        logger.info("Embedding service closed")


# Global embedding service instance
embedding_service = EmbeddingService()


async def get_embedding_service() -> EmbeddingService:
    """Dependency injection for embedding service."""
    if not embedding_service._model:
        await embedding_service.initialize()
    return embedding_service