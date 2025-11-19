"""
Similarity calculation service for computing match scores between job descriptions and resumes.
Handles cosine similarity calculation, score normalization, and batch processing.
"""

import logging
import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from pydantic import BaseModel, ConfigDict
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

class SimilarityResult(BaseModel):
    """Result of a similarity calculation between job and resume."""
    job_id: str
    resume_id: str
    similarity_score: float
    match_percentage: float
    confidence: float

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )


class BatchMatchResult(BaseModel):
    """Batch result of multiple similarity calculations."""
    matches: List[SimilarityResult]
    total_matches: int
    average_similarity: float

    model_config = ConfigDict(from_attributes=True)

# Similarity calculation class
class SimilarityService:
    """Service for calculating and managing similarity scores between documents."""


class SimilarityService:
    """Service for calculating similarity scores between embeddings."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        if embedding1 is None or embedding2 is None or len(embedding1) == 0 or len(embedding2) == 0:
            logger.warning("Empty or None embedding provided for similarity calculation")
            return 0.0
            
        if len(embedding1) != len(embedding2):
            logger.error(f"Embedding dimension mismatch: {len(embedding1)} vs {len(embedding2)}")
            return 0.0
        
        try:
            # Convert to numpy arrays for efficient computation
            vec1 = np.array(embedding1, dtype=np.float32)
            vec2 = np.array(embedding2, dtype=np.float32)
            
            # Calculate dot product
            dot_product = np.dot(vec1, vec2)
            
            # Calculate magnitudes
            magnitude1 = np.linalg.norm(vec1)
            magnitude2 = np.linalg.norm(vec2)
            
            # Avoid division by zero
            # Convert to float for comparison to avoid numpy array ambiguity
            if float(magnitude1) == 0 or float(magnitude2) == 0:
                logger.warning("Zero magnitude vector encountered")
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (magnitude1 * magnitude2)
            
            # Ensure result is within valid range
            similarity = max(-1.0, min(1.0, float(similarity)))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def normalize_to_percentage(self, similarity_score: float, method: str = "linear") -> float:
        """
        Normalize similarity score to 0-100% range.
        
        Args:
            similarity_score: Raw similarity score (typically -1 to 1)
            method: Normalization method ("linear", "sigmoid", "exponential")
            
        Returns:
            Normalized score as percentage (0-100)
        """
        try:
            if method == "linear":
                # Simple linear transformation from [-1, 1] to [0, 100]
                normalized = (similarity_score + 1) * 50
                
            elif method == "sigmoid":
                # Sigmoid transformation for more nuanced scoring
                # This gives more weight to higher similarities
                sigmoid_input = similarity_score * 5  # Scale input
                sigmoid_output = 1 / (1 + math.exp(-sigmoid_input))
                normalized = sigmoid_output * 100
                
            elif method == "exponential":
                # Exponential transformation for aggressive scoring
                # Only high similarities get good scores
                if similarity_score > 0:
                    normalized = (math.exp(similarity_score) - 1) / (math.e - 1) * 100
                else:
                    normalized = 0
                    
            else:
                logger.warning(f"Unknown normalization method: {method}, using linear")
                normalized = (similarity_score + 1) * 50
            
            # Ensure result is within valid range
            normalized = max(0.0, min(100.0, normalized))
            
            return round(normalized, 2)
            
        except Exception as e:
            logger.error(f"Error normalizing similarity score: {e}")
            return 0.0
    
    def calculate_confidence(self, similarity_score: float, embedding_quality: float = 1.0) -> float:
        """
        Calculate confidence score for the match result.
        
        Args:
            similarity_score: Raw similarity score
            embedding_quality: Quality indicator of the embeddings (0-1)
            
        Returns:
            Confidence score (0-1)
        """
        try:
            # Ensure similarity_score is a scalar float
            if isinstance(similarity_score, (list, np.ndarray)):
                similarity_score = float(similarity_score[0]) if len(similarity_score) > 0 else 0.0
            
            # Base confidence from similarity score
            base_confidence = abs(float(similarity_score))
            
            # Adjust for embedding quality
            adjusted_confidence = base_confidence * embedding_quality
            
            # Apply sigmoid to make confidence more interpretable
            confidence = 1 / (1 + math.exp(-5 * (adjusted_confidence - 0.5)))
            
            return round(confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    async def calculate_match_score(
        self, 
        job_embedding: List[float], 
        resume_embedding: List[float],
        job_id: str,
        resume_id: str,
        normalization_method: str = "sigmoid"
    ) -> SimilarityResult:
        """
        Calculate comprehensive match score between job and resume.
        
        Args:
            job_embedding: Job description embedding
            resume_embedding: Resume embedding
            job_id: Job identifier
            resume_id: Resume identifier
            normalization_method: Method for score normalization
            
        Returns:
            SimilarityResult with similarity and normalized scores
        """
        try:
            # Calculate raw similarity in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            similarity_score = await loop.run_in_executor(
                self.executor,
                self.calculate_cosine_similarity,
                job_embedding,
                resume_embedding
            )
            
            # Normalize to percentage
            match_percentage = self.normalize_to_percentage(similarity_score, normalization_method)
            
            # Calculate confidence
            confidence = self.calculate_confidence(similarity_score)
            
            return SimilarityResult(
                job_id=job_id,
                resume_id=resume_id,
                similarity_score=similarity_score,
                match_percentage=match_percentage,
                confidence=confidence
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Error calculating match score: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return SimilarityResult(
                job_id=job_id,
                resume_id=resume_id,
                similarity_score=0.0,
                match_percentage=0.0,
                confidence=0.0
            )
    
    async def batch_calculate_matches(
        self,
        job_embedding: List[float],
        resume_embeddings: List[Tuple[str, List[float]]],  # (resume_id, embedding)
        job_id: str,
        normalization_method: str = "sigmoid"
    ) -> BatchMatchResult:
        """
        Calculate match scores for multiple resumes against one job.
        
        Args:
            job_embedding: Job description embedding
            resume_embeddings: List of (resume_id, embedding) tuples
            job_id: Job identifier
            normalization_method: Method for score normalization
            
        Returns:
            BatchMatchResult with all match calculations
        """
        import time
        start_time = time.time()
        
        try:
            # Create tasks for concurrent processing
            tasks = []
            for resume_id, resume_embedding in resume_embeddings:
                task = self.calculate_match_score(
                    job_embedding=job_embedding,
                    resume_embedding=resume_embedding,
                    job_id=job_id,
                    resume_id=resume_id,
                    normalization_method=normalization_method
                )
                tasks.append(task)
            
            # Execute all calculations concurrently
            matches = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log errors
            valid_matches = []
            for match in matches:
                if isinstance(match, Exception):
                    logger.error(f"Error in batch match calculation: {match}")
                else:
                    valid_matches.append(match)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Processed {len(valid_matches)} matches in {processing_time:.2f}s")
            
            return BatchMatchResult(
                job_id=job_id,
                matches=valid_matches,
                processing_time=processing_time,
                total_comparisons=len(resume_embeddings)
            )
            
        except Exception as e:
            logger.error(f"Error in batch match calculation: {e}")
            processing_time = time.time() - start_time
            return BatchMatchResult(
                job_id=job_id,
                matches=[],
                processing_time=processing_time,
                total_comparisons=len(resume_embeddings)
            )
    
    def rank_matches(self, matches: List[SimilarityResult], sort_by: str = "match_percentage") -> List[SimilarityResult]:
        """
        Rank match results by specified criteria.
        
        Args:
            matches: List of match results to rank
            sort_by: Sorting criteria ("match_percentage", "similarity_score", "confidence")
            
        Returns:
            Sorted list of match results (highest first)
        """
        try:
            if sort_by == "match_percentage":
                return sorted(matches, key=lambda x: x.match_percentage, reverse=True)
            elif sort_by == "similarity_score":
                return sorted(matches, key=lambda x: x.similarity_score, reverse=True)
            elif sort_by == "confidence":
                return sorted(matches, key=lambda x: x.confidence, reverse=True)
            else:
                logger.warning(f"Unknown sort criteria: {sort_by}, using match_percentage")
                return sorted(matches, key=lambda x: x.match_percentage, reverse=True)
                
        except Exception as e:
            logger.error(f"Error ranking matches: {e}")
            return matches
    
    def filter_matches(
        self, 
        matches: List[SimilarityResult], 
        min_percentage: float = 0.0,
        min_confidence: float = 0.0,
        max_results: Optional[int] = None
    ) -> List[SimilarityResult]:
        """
        Filter match results based on criteria.
        
        Args:
            matches: List of match results to filter
            min_percentage: Minimum match percentage threshold
            min_confidence: Minimum confidence threshold
            max_results: Maximum number of results to return
            
        Returns:
            Filtered list of match results
        """
        try:
            # Apply filters
            filtered = [
                match for match in matches
                if match.match_percentage >= min_percentage and match.confidence >= min_confidence
            ]
            
            # Limit results if specified
            if max_results is not None:
                filtered = filtered[:max_results]
            
            logger.info(f"Filtered {len(matches)} matches to {len(filtered)} results")
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering matches: {e}")
            return matches
    
    def get_match_statistics(self, matches: List[SimilarityResult]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of match results.
        
        Args:
            matches: List of match results to analyze
            
        Returns:
            Dictionary of match statistics
        """
        if not matches:
            return {
                "count": 0,
                "avg_percentage": 0.0,
                "max_percentage": 0.0,
                "min_percentage": 0.0,
                "avg_confidence": 0.0
            }
        
        try:
            percentages = [match.match_percentage for match in matches]
            confidences = [match.confidence for match in matches]
            
            return {
                "count": len(matches),
                "avg_percentage": round(sum(percentages) / len(percentages), 2),
                "max_percentage": round(max(percentages), 2),
                "min_percentage": round(min(percentages), 2),
                "avg_confidence": round(sum(confidences) / len(confidences), 3),
                "above_50_percent": len([p for p in percentages if p >= 50]),
                "above_70_percent": len([p for p in percentages if p >= 70]),
                "above_90_percent": len([p for p in percentages if p >= 90])
            }
            
        except Exception as e:
            logger.error(f"Error calculating match statistics: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        logger.info("Similarity service executor shut down")


# Global similarity service instance
similarity_service = SimilarityService()


async def get_similarity_service() -> SimilarityService:
    """Dependency injection for similarity service."""
    return similarity_service