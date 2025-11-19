"""
Main matching engine that orchestrates embedding generation, similarity calculation,
and skill matching to provide comprehensive job-resume compatibility analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
import numpy as np

from app.services.embedding_service import get_embedding_service
from app.services.similarity_service import get_similarity_service, SimilarityResult
from app.services.skill_extraction_service import get_skill_extraction_service
from app.services.explanation_service import get_explanation_service
from app.services.cache_service import cache_service
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeRepository
from app.repositories.match_result import MatchResultRepository
from app.models.match_result import MatchResult as MatchResultModel

logger = logging.getLogger(__name__)


class ComprehensiveMatch(BaseModel):
    """Complete match result including similarity and skill analysis."""
    job_id: str
    resume_id: str
    overall_score: float
    similarity_score: float
    skill_match_percentage: float
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    explanation: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchingRequest(BaseModel):
    """Request for matching resumes against a job."""
    job_id: str
    resume_ids: Optional[List[str]] = None  # If None, match against all processed resumes
    include_explanations: bool = True
    min_score_threshold: float = 0.0
    max_results: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class MatchingEngine:
    """Main engine for job-resume matching using AI and skill analysis."""
    
    def __init__(self):
        self._embedding_service = None
        self._similarity_service = None
        self._skill_service = None
        self._explanation_service = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all required services."""
        if self._initialized:
            return
            
        try:
            self._embedding_service = await get_embedding_service()
            self._similarity_service = await get_similarity_service()
            self._skill_service = await get_skill_extraction_service()
            self._explanation_service = await get_explanation_service()
            
            self._initialized = True
            logger.info("Matching engine initialized successfully")
            
        except Exception as e:
            logger.exception(f"Failed to initialize matching engine: {e}")
            raise
    
    async def generate_job_embedding(self, job_repo: JobRepository, job_id: str) -> bool:
        """Generate and store embedding for a job description."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get job from database
            job = await job_repo.get(uuid.UUID(job_id))
            if not job:
                logger.error(f"Job not found: {job_id}")
                return False
            
            # Combine job text for embedding
            job_text = f"{job.title} {job.description} {job.requirements}"
            if job.skills_required:
                job_text += " " + " ".join(job.skills_required)
            
            # Generate embedding
            embedding = await self._embedding_service.generate_embedding(job_text)
            
            # Store embedding in database
            success = await job_repo.update_embedding(uuid.UUID(job_id), embedding)
            
            if success:
                logger.info(f"Generated embedding for job {job_id}")
            else:
                logger.error(f"Failed to store embedding for job {job_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating job embedding: {e}")
            return False
    
    async def generate_resume_embedding(self, resume_repo: ResumeRepository, resume_id: str) -> bool:
        """Generate and store embedding for a resume."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get resume from database
            resume = await resume_repo.get(uuid.UUID(resume_id))
            if not resume:
                logger.error(f"Resume not found: {resume_id}")
                return False
            
            # Use resume content for embedding
            resume_text = resume.content
            if resume.sections:
                # Add structured sections if available
                for section, content in resume.sections.items():
                    if content:
                        resume_text += f" {content}"
            
            # Generate embedding
            embedding = await self._embedding_service.generate_embedding(resume_text)
            
            # Store embedding in database
            success = await resume_repo.update_embedding(uuid.UUID(resume_id), embedding)
            
            if success:
                logger.info(f"Generated embedding for resume {resume_id}")
            else:
                logger.error(f"Failed to store embedding for resume {resume_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating resume embedding: {e}")
            return False
    
    async def batch_generate_resume_embeddings(
        self, 
        resume_repo: ResumeRepository, 
        resume_ids: List[str]
    ) -> Dict[str, bool]:
        """Generate embeddings for multiple resumes efficiently."""
        if not self._initialized:
            await self.initialize()
        
        results = {}
        
        try:
            # Get all resumes
            resumes = []
            for resume_id in resume_ids:
                resume = await resume_repo.get(uuid.UUID(resume_id))
                if resume:
                    resumes.append((resume_id, resume))
                else:
                    results[resume_id] = False
            
            if not resumes:
                return results
            
            # Prepare texts for batch processing
            texts = []
            for resume_id, resume in resumes:
                resume_text = resume.content
                if resume.sections:
                    for section, content in resume.sections.items():
                        if content:
                            resume_text += f" {content}"
                texts.append(resume_text)
            
            # Generate embeddings in batch
            embeddings = await self._embedding_service.batch_generate_embeddings(texts)
            
            # Store embeddings
            for i, (resume_id, resume) in enumerate(resumes):
                if i < len(embeddings):
                    success = await resume_repo.update_embedding(uuid.UUID(resume_id), embeddings[i])
                    results[resume_id] = success
                else:
                    results[resume_id] = False
            
            logger.info(f"Batch generated embeddings for {len(resumes)} resumes")
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            for resume_id in resume_ids:
                if resume_id not in results:
                    results[resume_id] = False
        
        return results
    
    async def calculate_comprehensive_match(
        self,
        job_repo: JobRepository,
        resume_repo: ResumeRepository,
        job_id: str,
        resume_id: str
    ) -> Optional[ComprehensiveMatch]:
        """Calculate comprehensive match between job and resume."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get job and resume
            job = await job_repo.get(uuid.UUID(job_id))
            resume = await resume_repo.get(uuid.UUID(resume_id))
            
            if not job or not resume:
                logger.error(f"Job or resume not found: {job_id}, {resume_id}")
                return None
            
            # Ensure embeddings exist
            if job.embedding is None or (isinstance(job.embedding, (list, np.ndarray)) and len(job.embedding) == 0):
                await self.generate_job_embedding(job_repo, job_id)
                job = await job_repo.get(uuid.UUID(job_id))  # Refresh
            
            if resume.embedding is None or (isinstance(resume.embedding, (list, np.ndarray)) and len(resume.embedding) == 0):
                await self.generate_resume_embedding(resume_repo, resume_id)
                resume = await resume_repo.get(uuid.UUID(resume_id))  # Refresh
            
            if job.embedding is None or resume.embedding is None:
                logger.error("Failed to generate required embeddings")
                return None
            
            if (isinstance(job.embedding, (list, np.ndarray)) and len(job.embedding) == 0) or \
               (isinstance(resume.embedding, (list, np.ndarray)) and len(resume.embedding) == 0):
                logger.error("Empty embeddings found")
                return None
            
            # Calculate similarity score
            similarity_result = await self._similarity_service.calculate_match_score(
                job_embedding=job.embedding,
                resume_embedding=resume.embedding,
                job_id=job_id,
                resume_id=resume_id
            )
            
            # Perform skill analysis
            job_text = f"{job.title} {job.description} {job.requirements}"
            resume_text = resume.content
            
            skill_analysis = await self._skill_service.analyze_skill_gaps(job_text, resume_text)
            
            # Calculate overall score (weighted combination)
            similarity_weight = 0.7
            skill_weight = 0.3
            
            overall_score = (
                similarity_result.match_percentage * similarity_weight +
                skill_analysis['skill_match']['match_percentage'] * skill_weight
            )

            # Generate explanation using template-based method (no Anthropic API call)
            skill_analysis_formatted = {
                'matched_skills': skill_analysis['skill_match']['matched_skills'],
                'missing_skills': skill_analysis['skill_match']['missing_skills']
            }

            # Use the internal template-based explanation generator
            explanation = self._generate_match_explanation(
                overall_score,
                skill_analysis,
                job.title,
                resume.candidate_name
            )
            
            return ComprehensiveMatch(
                job_id=job_id,
                resume_id=resume_id,
                overall_score=round(overall_score, 2),
                similarity_score=similarity_result.match_percentage,
                skill_match_percentage=skill_analysis['skill_match']['match_percentage'],
                matched_skills=skill_analysis['skill_match']['matched_skills'],
                missing_skills=skill_analysis['skill_match']['missing_skills'],
                additional_skills=skill_analysis['skill_match']['additional_skills'],
                explanation=explanation,
                confidence=similarity_result.confidence,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Error calculating comprehensive match: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def match_resumes_to_job(
        self,
        job_repo: JobRepository,
        resume_repo: ResumeRepository,
        match_result_repo: MatchResultRepository,
        request: MatchingRequest
    ) -> List[ComprehensiveMatch]:
        """Match multiple resumes against a job and store results."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get target resumes
            if request.resume_ids:
                resumes = []
                for resume_id in request.resume_ids:
                    # Skip empty or invalid resume IDs
                    if not resume_id or not resume_id.strip():
                        logger.warning(f"Skipping empty resume_id in match request")
                        continue
                    try:
                        resume = await resume_repo.get(uuid.UUID(resume_id))
                        if resume:
                            resumes.append(resume)
                        else:
                            logger.warning(f"Resume {resume_id} not found")
                    except ValueError as e:
                        logger.warning(f"Invalid resume_id format: {resume_id} - {e}")
                        continue
            else:
                # Get all processed resumes
                resumes = await resume_repo.get_processed_resumes(limit=1000)
            
            if not resumes:
                logger.warning("No resumes found for matching")
                return []
            
            resume_ids = [str(resume.id) for resume in resumes]
            
            # Check cache first
            cached_results = await cache_service.get_cached_match_results(
                request.job_id, resume_ids
            )
            
            if cached_results:
                logger.info(f"Retrieved {len(cached_results)} cached match results for job {request.job_id}")
                
                # Convert cached results back to ComprehensiveMatch objects
                successful_matches = []
                for result in cached_results:
                    match = ComprehensiveMatch(
                        job_id=result["job_id"],
                        resume_id=result["resume_id"],
                        overall_score=result["overall_score"],
                        similarity_score=result["similarity_score"],
                        skill_match_percentage=result["skill_match_percentage"],
                        matched_skills=result["matched_skills"],
                        missing_skills=result["missing_skills"],
                        additional_skills=result["additional_skills"],
                        explanation=result["explanation"],
                        confidence=result["confidence"],
                        created_at=datetime.fromisoformat(result["created_at"])
                    )
                    if match.overall_score >= request.min_score_threshold:
                        successful_matches.append(match)
                
                # Sort and limit results
                successful_matches.sort(key=lambda x: x.overall_score, reverse=True)
                if request.max_results:
                    successful_matches = successful_matches[:request.max_results]
                
                return successful_matches
            
            logger.info(f"Matching {len(resumes)} resumes against job {request.job_id}")
            
            # Calculate matches concurrently (but limit concurrency)
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent matches
            
            async def calculate_single_match(resume):
                async with semaphore:
                    return await self.calculate_comprehensive_match(
                        job_repo, resume_repo, request.job_id, str(resume.id)
                    )
            
            # Execute all matches
            match_tasks = [calculate_single_match(resume) for resume in resumes]
            match_results = await asyncio.gather(*match_tasks, return_exceptions=True)
            
            # Filter successful results
            successful_matches = []
            for result in match_results:
                if isinstance(result, ComprehensiveMatch):
                    if result.overall_score >= request.min_score_threshold:
                        successful_matches.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Match calculation failed: {result}")
            
            # Sort by overall score
            successful_matches.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Limit results if requested
            if request.max_results:
                successful_matches = successful_matches[:request.max_results]
            
            # Cache the results
            cache_data = []
            for match in successful_matches:
                cache_data.append({
                    "job_id": match.job_id,
                    "resume_id": match.resume_id,
                    "overall_score": match.overall_score,
                    "similarity_score": match.similarity_score,
                    "skill_match_percentage": match.skill_match_percentage,
                    "matched_skills": match.matched_skills,
                    "missing_skills": match.missing_skills,
                    "additional_skills": match.additional_skills,
                    "explanation": match.explanation,
                    "confidence": match.confidence,
                    "created_at": match.created_at.isoformat()
                })
            
            await cache_service.cache_match_results(
                request.job_id, resume_ids, cache_data, expire_hours=6
            )
            
            # Store results in database
            await self._store_match_results(match_result_repo, successful_matches)
            
            logger.info(f"Completed matching: {len(successful_matches)} results above threshold")
            
            return successful_matches
            
        except Exception as e:
            logger.error(f"Error in resume matching: {e}")
            return []
    
    async def _store_match_results(
        self, 
        match_result_repo: MatchResultRepository, 
        matches: List[ComprehensiveMatch]
    ):
        """Store match results in the database (upsert: update if exists, create if not)."""
        try:
            for match in matches:
                # Prepare skill_matches JSON
                skill_matches = {
                    "matched": match.matched_skills,
                    "missing": match.missing_skills,
                    "additional": match.additional_skills
                }
                
                match_data = {
                    "job_id": uuid.UUID(match.job_id),
                    "resume_id": uuid.UUID(match.resume_id),
                    "match_score": match.overall_score,
                    "confidence_score": match.confidence,
                    "explanation": match.explanation,
                    "key_strengths": match.matched_skills,
                    "missing_skills": match.missing_skills,
                    "skill_matches": skill_matches,
                    "skills_score": match.skill_match_percentage
                }
                
                # Check if match result already exists
                existing_match = await match_result_repo.get_match(
                    uuid.UUID(match.job_id),
                    uuid.UUID(match.resume_id)
                )
                
                if existing_match:
                    # Update existing match result
                    await match_result_repo.update(existing_match.id, match_data)
                    logger.debug(f"Updated existing match result for job {match.job_id} and resume {match.resume_id}")
                else:
                    # Create new match result
                    await match_result_repo.create(match_data)
                    logger.debug(f"Created new match result for job {match.job_id} and resume {match.resume_id}")
            
            logger.info(f"Stored {len(matches)} match results in database")
            
        except Exception as e:
            logger.error(f"Error storing match results: {e}")
    
    def _generate_match_explanation(
        self,
        similarity_score: float,
        skill_analysis: Dict[str, Any],
        job_title: str,
        candidate_name: str
    ) -> str:
        """Generate human-readable explanation for the match."""
        try:
            explanation_parts = []
            
            # Overall assessment
            if similarity_score >= 80:
                explanation_parts.append(f"{candidate_name} is an excellent match for the {job_title} position.")
            elif similarity_score >= 60:
                explanation_parts.append(f"{candidate_name} is a good match for the {job_title} position.")
            elif similarity_score >= 40:
                explanation_parts.append(f"{candidate_name} is a moderate match for the {job_title} position.")
            else:
                explanation_parts.append(f"{candidate_name} has limited alignment with the {job_title} position.")
            
            # Skill analysis
            skill_match = skill_analysis.get('skill_match', {})
            matched_skills = skill_match.get('matched_skills', [])
            missing_skills = skill_match.get('missing_skills', [])
            
            if matched_skills:
                if len(matched_skills) <= 3:
                    explanation_parts.append(f"Key matching skills include: {', '.join(matched_skills)}.")
                else:
                    explanation_parts.append(f"Strong skills alignment with {len(matched_skills)} matching competencies including {', '.join(matched_skills[:3])}.")
            
            if missing_skills:
                if len(missing_skills) <= 3:
                    explanation_parts.append(f"Areas for development: {', '.join(missing_skills)}.")
                else:
                    explanation_parts.append(f"Some skill gaps identified in {len(missing_skills)} areas including {', '.join(missing_skills[:3])}.")
            
            # Recommendation
            if similarity_score >= 70 and skill_match.get('match_percentage', 0) >= 60:
                explanation_parts.append("Recommended for interview consideration.")
            elif similarity_score >= 50:
                explanation_parts.append("Consider for further review based on specific requirements.")
            else:
                explanation_parts.append("May not be the best fit for current requirements.")
            
            return " ".join(explanation_parts)
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return f"Match score: {similarity_score}%. Detailed analysis available in skill breakdown."
    
    async def get_match_statistics(
        self, 
        match_result_repo: MatchResultRepository, 
        job_id: str
    ) -> Dict[str, Any]:
        """Get matching statistics for a job."""
        try:
            matches = await match_result_repo.get_by_job_id(uuid.UUID(job_id))
            
            if not matches:
                return {
                    "total_candidates": 0,
                    "avg_score": 0.0,
                    "top_score": 0.0,
                    "candidates_above_70": 0,
                    "candidates_above_50": 0,
                    "most_common_missing_skills": []
                }
            
            scores = [match.match_score for match in matches]
            all_missing_skills = []
            for match in matches:
                if match.missing_skills:
                    all_missing_skills.extend(match.missing_skills)
            
            # Count missing skills frequency
            skill_counts = {}
            for skill in all_missing_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            most_common_missing = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total_candidates": len(matches),
                "avg_score": round(sum(scores) / len(scores), 2),
                "top_score": round(max(scores), 2),
                "candidates_above_70": len([s for s in scores if s >= 70]),
                "candidates_above_50": len([s for s in scores if s >= 50]),
                "most_common_missing_skills": [skill for skill, count in most_common_missing]
            }
            
        except Exception as e:
            logger.error(f"Error getting match statistics: {e}")
            return {"error": str(e)}


# Global matching engine instance
matching_engine = MatchingEngine()


async def get_matching_engine() -> MatchingEngine:
    """Dependency injection for matching engine."""
    if not matching_engine._initialized:
        await matching_engine.initialize()
    return matching_engine