"""
API endpoints for explanation service functionality.
Handles match explanation generation and formatting.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.explanation_service import get_explanation_service, ExplanationService
from app.schemas.explanation import (
    ExplanationRequest, ExplanationResponse, BatchExplanationRequest, 
    BatchExplanationResponse, ExplanationStats
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=ExplanationResponse)
async def generate_explanation(
    request: ExplanationRequest,
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Generate a structured explanation for a job-resume match.
    
    This endpoint takes job description, resume content, match score, and skill analysis
    to generate a comprehensive explanation with strengths, concerns, and recommendations.
    """
    try:
        logger.info(f"Generating explanation for match score: {request.match_score}%")
        
        explanation_response = await explanation_service.generate_structured_explanation(request)
        
        logger.info(f"Successfully generated {explanation_response.explanation_source} explanation")
        return explanation_response
        
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/generate-batch", response_model=BatchExplanationResponse)
async def generate_batch_explanations(
    request: BatchExplanationRequest,
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Generate multiple explanations efficiently with concurrency control.
    
    This endpoint processes multiple explanation requests in parallel,
    useful for batch processing of candidate matches.
    """
    try:
        logger.info(f"Generating batch explanations for {len(request.explanations)} requests")
        
        if len(request.explanations) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 explanations per batch request"
            )
        
        batch_response = await explanation_service.generate_batch_explanations(request)
        
        logger.info(f"Batch processing completed: {batch_response.successful_count} successful, "
                   f"{batch_response.failed_count} failed")
        
        return batch_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate batch explanations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch explanations: {str(e)}"
        )


@router.post("/improvement-suggestions")
async def get_improvement_suggestions(
    missing_skills: List[str],
    match_score: float,
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Get specific improvement suggestions for candidates.
    
    This endpoint provides actionable recommendations based on missing skills
    and current match score to help candidates improve their profiles.
    """
    try:
        if not 0 <= match_score <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Match score must be between 0 and 100"
            )
        
        suggestions = await explanation_service.create_improvement_suggestions(
            missing_skills, match_score
        )
        
        return {
            "suggestions": suggestions,
            "missing_skills_count": len(missing_skills),
            "match_score": match_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate improvement suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate improvement suggestions: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_explanation_stats(
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Get statistics about the explanation service usage and performance.
    
    Returns information about service configuration, cache usage, and performance metrics.
    """
    try:
        stats = await explanation_service.get_explanation_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get explanation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get explanation stats: {str(e)}"
        )


@router.delete("/cache")
async def clear_explanation_cache(
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Clear all cached explanations.
    
    This endpoint clears the Redis cache for explanations, forcing fresh generation
    for subsequent requests. Useful for testing or when explanation logic changes.
    """
    try:
        success = await explanation_service.clear_cache()
        
        if success:
            return {"message": "Explanation cache cleared successfully"}
        else:
            return {"message": "Cache clearing not available (Redis not configured)"}
        
    except Exception as e:
        logger.error(f"Failed to clear explanation cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear explanation cache: {str(e)}"
        )


@router.post("/test-template")
async def test_template_explanation(
    job_description: str,
    resume_content: str,
    match_score: float,
    matched_skills: List[str] = [],
    missing_skills: List[str] = [],
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Test template-based explanation generation (fallback mode).
    
    This endpoint forces the use of template-based explanations for testing
    and validation purposes, bypassing LLM generation.
    """
    try:
        if not 0 <= match_score <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Match score must be between 0 and 100"
            )
        
        skill_analysis = {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_percentage': len(matched_skills) / (len(matched_skills) + len(missing_skills)) * 100 if (matched_skills or missing_skills) else 0
        }
        
        # Force template explanation by temporarily disabling LLM
        original_client = explanation_service._anthropic_client
        explanation_service._anthropic_client = None
        
        try:
            explanation = await explanation_service.generate_explanation(
                job_description, resume_content, match_score, skill_analysis
            )
            
            return {
                "explanation": explanation,
                "source": "template",
                "match_score": match_score,
                "skill_analysis": skill_analysis
            }
        finally:
            # Restore original client
            explanation_service._anthropic_client = original_client
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate template explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template explanation: {str(e)}"
        )