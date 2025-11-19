"""
Explanation service for generating human-readable match explanations using Anthropic's Claude.
Handles LLM integration, prompt templates, and fallback explanations.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
import json
import re
from datetime import datetime, timedelta
import hashlib
import redis.asyncio as redis
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.exceptions import ExplanationServiceError, ExternalServiceError, RateLimitError
from app.core.error_handler import error_handler, RetryHandler, explanation_circuit_breaker, GracefulDegradation
from app.core.logging_config import performance_logger
from app.schemas.explanation import (
    ExplanationResponse, MatchExplanation, SkillAnalysis, ImprovementSuggestion,
    ExplanationRequest, BatchExplanationRequest, BatchExplanationResponse
)

logger = logging.getLogger(__name__)


class ExplanationService:
    """Service for generating match explanations using Anthropic Claude."""
    
    def __init__(self):
        self._anthropic_client = None
        self._redis_client = None
        self.model_name = "claude-3-haiku-20240307"  # Fast and cost-effective model
        self.max_tokens = 1000
        self.cache_ttl = 3600  # 1 hour cache for explanations
        
    async def initialize(self):
        """Initialize the Anthropic client and Redis connection."""
        try:
            # Initialize Anthropic client
            logger.info(f"Attempting to initialize Anthropic client. API key present: {bool(settings.ANTHROPIC_API_KEY)}")
            if settings.ANTHROPIC_API_KEY:
                try:
                    self._anthropic_client = AsyncAnthropic(
                        api_key=settings.ANTHROPIC_API_KEY
                    )
                    # Test the client by checking if it has the messages attribute
                    if not hasattr(self._anthropic_client, 'messages'):
                        logger.error("Anthropic client missing 'messages' attribute. Check anthropic package version.")
                        self._anthropic_client = None
                    else:
                        logger.info("Anthropic client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Anthropic client: {e}")
                    self._anthropic_client = None
            else:
                logger.warning("ANTHROPIC_API_KEY not provided, explanations will use fallback templates")
            
            # Initialize Redis connection for caching
            try:
                self._redis_client = redis.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                    decode_responses=True
                )
                await self._redis_client.ping()
                logger.info("Redis connection established for explanation cache")
            except Exception as e:
                logger.warning(f"Redis connection failed, caching disabled: {e}")
                self._redis_client = None
                
        except Exception as e:
            logger.error(f"Failed to initialize explanation service: {e}")
            raise
    
    def _get_explanation_hash(self, job_desc: str, resume: str, match_score: float, 
                            skill_analysis: Dict) -> str:
        """Generate a hash for explanation caching."""
        content = f"{job_desc[:500]}{resume[:500]}{match_score}{json.dumps(skill_analysis, sort_keys=True)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def _get_cached_explanation(self, cache_key: str) -> Optional[str]:
        """Retrieve cached explanation from Redis."""
        if not self._redis_client:
            return None
            
        try:
            cached_explanation = await self._redis_client.get(f"explanation:{cache_key}")
            if cached_explanation:
                logger.debug("Retrieved explanation from cache")
                return cached_explanation
        except Exception as e:
            logger.warning(f"Failed to retrieve cached explanation: {e}")
        
        return None
    
    async def _cache_explanation(self, cache_key: str, explanation: str):
        """Cache explanation in Redis."""
        if not self._redis_client:
            return
            
        try:
            await self._redis_client.setex(
                f"explanation:{cache_key}", 
                self.cache_ttl, 
                explanation
            )
            logger.debug("Cached explanation successfully")
        except Exception as e:
            logger.warning(f"Failed to cache explanation: {e}")
    
    def _create_explanation_prompt(self, job_desc: str, resume: str, match_score: float, 
                                 skill_analysis: Dict) -> str:
        """Create a structured prompt for explanation generation."""
        
        matched_skills = skill_analysis.get('matched_skills', [])
        missing_skills = skill_analysis.get('missing_skills', [])
        
        prompt = f"""You are an expert HR analyst. Analyze the match between this job description and candidate resume, then provide a clear, professional explanation.

Job Description:
{job_desc[:2000]}

Candidate Resume:
{resume[:2000]}

Match Score: {match_score:.1f}%

Skill Analysis:
- Matched Skills: {', '.join(matched_skills[:10]) if matched_skills else 'None identified'}
- Missing Skills: {', '.join(missing_skills[:10]) if missing_skills else 'None identified'}

Please provide a structured explanation with:

1. **Overall Assessment** (2-3 sentences about the match quality)
2. **Key Strengths** (3-5 specific points where the candidate aligns well)
3. **Areas of Concern** (3-5 specific gaps or misalignments)
4. **Recommendation** (1-2 sentences with hiring recommendation)

Keep the explanation professional, specific, and actionable. Focus on concrete skills, experience, and qualifications mentioned in both documents."""

        return prompt
    
    @explanation_circuit_breaker
    async def _generate_llm_explanation(self, job_desc: str, resume: str, 
                                      match_score: float, skill_analysis: Dict) -> Optional[str]:
        """Generate explanation using Anthropic Claude with error handling."""
        if not self._anthropic_client:
            return None
            
        try:
            prompt = self._create_explanation_prompt(job_desc, resume, match_score, skill_analysis)
            
            # Use retry logic for LLM calls
            explanation = await RetryHandler.retry_with_backoff(
                self._call_anthropic_api,
                max_retries=2,
                base_delay=2.0,
                exceptions=(ExplanationServiceError, ExternalServiceError, RateLimitError),
                prompt=prompt
            )
            
            logger.debug(f"Generated LLM explanation with {len(explanation)} characters")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate LLM explanation: {e}")
            return None
    
    async def _call_anthropic_api(self, prompt: str) -> str:
        """Make API call to Anthropic with proper error handling."""
        try:
            # Make API call with rate limiting and error handling
            response = await self._anthropic_client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for more consistent explanations
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            raise await error_handler.handle_ai_service_error(
                e,
                service_name="explanation",
                operation="llm_explanation"
            )
    
    def _create_template_explanation(self, job_desc: str, resume: str, 
                                   match_score: float, skill_analysis: Dict) -> str:
        """Create fallback template-based explanation."""
        
        matched_skills = skill_analysis.get('matched_skills', [])
        missing_skills = skill_analysis.get('missing_skills', [])
        
        # Determine match quality
        if match_score >= 80:
            assessment = "This candidate shows excellent alignment with the job requirements."
            recommendation = "Strongly recommended for interview."
        elif match_score >= 60:
            assessment = "This candidate shows good potential with some areas for development."
            recommendation = "Recommended for interview with focus on addressing skill gaps."
        elif match_score >= 40:
            assessment = "This candidate shows moderate alignment with mixed qualifications."
            recommendation = "Consider for interview if other candidates are limited."
        else:
            assessment = "This candidate shows limited alignment with the job requirements."
            recommendation = "Not recommended unless significant training is planned."
        
        # Build strengths section
        strengths = []
        if matched_skills:
            strengths.append(f"Possesses {len(matched_skills)} relevant skills including {', '.join(matched_skills[:3])}")
        if match_score >= 50:
            strengths.append("Resume content shows good semantic alignment with job description")
        if not strengths:
            strengths.append("Basic qualifications present in resume")
        
        # Build concerns section
        concerns = []
        if missing_skills:
            concerns.append(f"Missing {len(missing_skills)} key skills: {', '.join(missing_skills[:3])}")
        if match_score < 60:
            concerns.append("Limited alignment between resume content and job requirements")
        if not concerns:
            concerns.append("No significant concerns identified")
        
        explanation = f"""**Overall Assessment**
{assessment} The match score of {match_score:.1f}% reflects the degree of alignment between the candidate's background and the position requirements.

**Key Strengths**
{chr(10).join(f"• {strength}" for strength in strengths[:5])}

**Areas of Concern**
{chr(10).join(f"• {concern}" for concern in concerns[:5])}

**Recommendation**
{recommendation}"""

        return explanation
    
    async def generate_explanation(self, job_desc: str, resume: str, match_score: float, 
                                 skill_analysis: Dict) -> str:
        """
        Generate a comprehensive explanation for the match score with error handling.
        
        Args:
            job_desc: Job description text
            resume: Resume text
            match_score: Match score percentage (0-100)
            skill_analysis: Dictionary with matched_skills and missing_skills
            
        Returns:
            Formatted explanation string
        """
        with performance_logger.time_operation(
            "explanation_generation",
            match_score=match_score,
            job_desc_length=len(job_desc),
            resume_length=len(resume)
        ):
            # Check cache first
            cache_key = self._get_explanation_hash(job_desc, resume, match_score, skill_analysis)
            cached_explanation = await self._get_cached_explanation(cache_key)
            if cached_explanation:
                return cached_explanation
            
            # Try to generate LLM explanation
            explanation = await self._generate_llm_explanation(job_desc, resume, match_score, skill_analysis)
            
            # Fall back to template if LLM fails
            if not explanation:
                logger.info("Using template-based explanation as fallback")
                explanation = GracefulDegradation.template_explanation_fallback(
                    match_score,
                    skill_analysis.get('matched_skills', []),
                    skill_analysis.get('missing_skills', [])
                )
            
            # Cache the result
            await self._cache_explanation(cache_key, explanation)
            
            return explanation
    
    def _parse_structured_explanation(self, explanation_text: str) -> MatchExplanation:
        """Parse LLM explanation text into structured format."""
        try:
            # Initialize default values
            overall_assessment = ""
            key_strengths = []
            areas_of_concern = []
            recommendation = ""
            confidence_level = "Medium"
            
            # Split explanation into sections
            sections = explanation_text.split('\n\n')
            current_section = None
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Identify section headers
                if section.startswith('**Overall Assessment**') or section.startswith('Overall Assessment'):
                    current_section = 'assessment'
                    overall_assessment = re.sub(r'\*\*.*?\*\*', '', section).strip()
                elif section.startswith('**Key Strengths**') or section.startswith('Key Strengths'):
                    current_section = 'strengths'
                elif section.startswith('**Areas of Concern**') or section.startswith('Areas of Concern'):
                    current_section = 'concerns'
                elif section.startswith('**Recommendation**') or section.startswith('Recommendation'):
                    current_section = 'recommendation'
                    recommendation = re.sub(r'\*\*.*?\*\*', '', section).strip()
                else:
                    # Parse bullet points or content based on current section
                    if current_section == 'strengths':
                        # Extract bullet points
                        bullets = re.findall(r'[•\-\*]\s*(.+)', section)
                        key_strengths.extend([bullet.strip() for bullet in bullets])
                    elif current_section == 'concerns':
                        bullets = re.findall(r'[•\-\*]\s*(.+)', section)
                        areas_of_concern.extend([bullet.strip() for bullet in bullets])
                    elif current_section == 'assessment' and not overall_assessment:
                        overall_assessment = section
                    elif current_section == 'recommendation' and not recommendation:
                        recommendation = section
            
            # Determine confidence level based on content
            if "excellent" in explanation_text.lower() or "strong" in explanation_text.lower():
                confidence_level = "High"
            elif "limited" in explanation_text.lower() or "concern" in explanation_text.lower():
                confidence_level = "Low"
            
            return MatchExplanation(
                overall_assessment=overall_assessment or "Match analysis completed",
                key_strengths=key_strengths[:5],  # Limit to top 5
                areas_of_concern=areas_of_concern[:5],  # Limit to top 5
                recommendation=recommendation or "Review based on specific requirements",
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse structured explanation: {e}")
            # Return basic structure with original text
            return MatchExplanation(
                overall_assessment=explanation_text[:200] + "..." if len(explanation_text) > 200 else explanation_text,
                key_strengths=["Analysis available in full explanation"],
                areas_of_concern=["See detailed explanation for concerns"],
                recommendation="Review full explanation for recommendation",
                confidence_level="Medium"
            )
    
    async def generate_structured_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Generate a structured explanation response."""
        try:
            # Generate the explanation text
            explanation_text = await self.generate_explanation(
                request.job_description,
                request.resume_content,
                request.match_score,
                request.skill_analysis
            )
            
            # Parse into structured format
            structured_explanation = self._parse_structured_explanation(explanation_text)
            
            # Create skill analysis
            skill_analysis = SkillAnalysis(
                matched_skills=request.skill_analysis.get('matched_skills', []),
                missing_skills=request.skill_analysis.get('missing_skills', []),
                additional_skills=request.skill_analysis.get('additional_skills', []),
                match_percentage=request.skill_analysis.get('match_percentage', 0.0)
            )
            
            # Generate improvement suggestions if requested
            improvement_suggestions = []
            if request.include_improvements:
                suggestions = await self.create_improvement_suggestions(
                    skill_analysis.missing_skills,
                    request.match_score
                )
                
                # Convert to structured format
                for i, suggestion in enumerate(suggestions):
                    priority = "High" if i < 2 else "Medium" if i < 4 else "Low"
                    impact = "High" if "skill" in suggestion.lower() else "Medium"
                    category = "Technical Skills" if any(tech in suggestion.lower() 
                                                       for tech in ['skill', 'course', 'certification']) else "Experience"
                    
                    improvement_suggestions.append(ImprovementSuggestion(
                        category=category,
                        suggestion=suggestion,
                        priority=priority,
                        estimated_impact=impact
                    ))
            
            # Determine explanation source
            explanation_source = "LLM" if self._anthropic_client else "Template"
            
            return ExplanationResponse(
                match_score=request.match_score,
                similarity_score=request.skill_analysis.get('similarity_score', request.match_score),
                skill_analysis=skill_analysis,
                explanation=structured_explanation,
                improvement_suggestions=improvement_suggestions,
                explanation_source=explanation_source
            )
            
        except Exception as e:
            logger.error(f"Failed to generate structured explanation: {e}")
            # Return minimal response
            return ExplanationResponse(
                match_score=request.match_score,
                similarity_score=request.match_score,
                skill_analysis=SkillAnalysis(
                    matched_skills=request.skill_analysis.get('matched_skills', []),
                    missing_skills=request.skill_analysis.get('missing_skills', [])
                ),
                explanation=MatchExplanation(
                    overall_assessment="Unable to generate detailed explanation",
                    key_strengths=["Analysis temporarily unavailable"],
                    areas_of_concern=["Please try again later"],
                    recommendation="Manual review recommended",
                    confidence_level="Low"
                ),
                explanation_source="Error"
            )
    
    async def generate_batch_explanations(self, request: BatchExplanationRequest) -> BatchExplanationResponse:
        """Generate multiple explanations efficiently."""
        start_time = datetime.utcnow()
        explanations = []
        successful_count = 0
        failed_count = 0
        
        # Process explanations with concurrency limit
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def process_single_explanation(explanation_request: ExplanationRequest):
            nonlocal successful_count, failed_count
            async with semaphore:
                try:
                    result = await self.generate_structured_explanation(explanation_request)
                    successful_count += 1
                    return result
                except Exception as e:
                    logger.error(f"Failed to generate explanation: {e}")
                    failed_count += 1
                    return None
        
        # Execute all explanations
        tasks = [process_single_explanation(req) for req in request.explanations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, ExplanationResponse):
                explanations.append(result)
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        return BatchExplanationResponse(
            explanations=explanations,
            successful_count=successful_count,
            failed_count=failed_count,
            total_time=total_time
        )
    
    async def create_improvement_suggestions(self, missing_skills: List[str], 
                                           match_score: float) -> List[str]:
        """
        Create specific improvement suggestions for candidates.
        
        Args:
            missing_skills: List of skills the candidate is missing
            match_score: Current match score
            
        Returns:
            List of actionable improvement suggestions
        """
        suggestions = []
        
        if missing_skills:
            # Group skills by category for better suggestions
            technical_skills = [skill for skill in missing_skills if any(
                tech in skill.lower() for tech in ['python', 'java', 'sql', 'aws', 'docker', 'react']
            )]
            soft_skills = [skill for skill in missing_skills if any(
                soft in skill.lower() for soft in ['leadership', 'communication', 'management', 'teamwork']
            )]
            
            if technical_skills:
                suggestions.append(f"Consider gaining experience in: {', '.join(technical_skills[:3])}")
                suggestions.append("Take online courses or certifications in the missing technical skills")
            
            if soft_skills:
                suggestions.append(f"Highlight or develop: {', '.join(soft_skills[:2])}")
                suggestions.append("Include specific examples demonstrating these soft skills in your resume")
        
        # Score-based suggestions
        if match_score < 40:
            suggestions.append("Consider targeting roles that better match your current skill set")
            suggestions.append("Significantly expand your skills in this domain before applying")
        elif match_score < 70:
            suggestions.append("Tailor your resume to better highlight relevant experience")
            suggestions.append("Consider gaining 1-2 additional key skills to improve your match")
        
        # General suggestions
        suggestions.extend([
            "Use keywords from the job description in your resume",
            "Quantify your achievements with specific metrics and results",
            "Ensure your resume clearly demonstrates relevant experience"
        ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    async def get_explanation_stats(self) -> Dict[str, Any]:
        """Get statistics about the explanation service."""
        stats = {
            "anthropic_configured": self._anthropic_client is not None,
            "model_name": self.model_name,
            "cache_enabled": self._redis_client is not None,
            "cache_ttl": self.cache_ttl
        }
        
        if self._redis_client:
            try:
                # Get cache statistics for explanations
                keys = await self._redis_client.keys("explanation:*")
                stats["cached_explanations"] = len(keys)
            except Exception as e:
                logger.warning(f"Failed to get explanation cache stats: {e}")
        
        return stats
    
    async def clear_cache(self) -> bool:
        """Clear all cached explanations."""
        if not self._redis_client:
            return False
            
        try:
            keys = await self._redis_client.keys("explanation:*")
            if keys:
                await self._redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached explanations")
            return True
        except Exception as e:
            logger.error(f"Failed to clear explanation cache: {e}")
            return False
    
    async def close(self):
        """Clean up resources."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Closed Redis connection for explanation service")


# Global explanation service instance
explanation_service = ExplanationService()


async def get_explanation_service() -> ExplanationService:
    """Dependency injection for explanation service."""
    if not explanation_service._anthropic_client and not explanation_service._redis_client:
        await explanation_service.initialize()
    return explanation_service