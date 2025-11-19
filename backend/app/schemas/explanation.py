"""
Schemas for explanation service responses and structured output formatting.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SkillAnalysis(BaseModel):
    """Structured skill analysis for explanations."""
    matched_skills: List[str] = Field(default_factory=list, description="Skills that match between job and resume")
    missing_skills: List[str] = Field(default_factory=list, description="Skills required by job but missing from resume")
    additional_skills: List[str] = Field(default_factory=list, description="Extra skills candidate has beyond requirements")
    match_percentage: float = Field(ge=0, le=100, description="Percentage of required skills that candidate possesses")


class MatchExplanation(BaseModel):
    """Structured explanation for a job-resume match."""
    overall_assessment: str = Field(description="High-level summary of the match quality")
    key_strengths: List[str] = Field(description="Specific strengths and positive alignments")
    areas_of_concern: List[str] = Field(description="Gaps, weaknesses, or areas needing development")
    recommendation: str = Field(description="Hiring recommendation based on the analysis")
    confidence_level: str = Field(description="Confidence in the assessment (High/Medium/Low)")


class ImprovementSuggestion(BaseModel):
    """Structured improvement suggestion for candidates."""
    category: str = Field(description="Category of improvement (Technical Skills, Experience, etc.)")
    suggestion: str = Field(description="Specific actionable suggestion")
    priority: str = Field(description="Priority level (High/Medium/Low)")
    estimated_impact: str = Field(description="Expected impact on match score")


class ExplanationResponse(BaseModel):
    """Complete explanation response with structured formatting."""
    match_score: float = Field(ge=0, le=100, description="Overall match score percentage")
    similarity_score: float = Field(ge=0, le=100, description="Semantic similarity score")
    skill_analysis: SkillAnalysis = Field(description="Detailed skill analysis")
    explanation: MatchExplanation = Field(description="Structured match explanation")
    improvement_suggestions: List[ImprovementSuggestion] = Field(
        default_factory=list, 
        description="Suggestions for improving match score"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When explanation was generated")
    explanation_source: str = Field(description="Source of explanation (LLM/Template)")


class ExplanationRequest(BaseModel):
    """Request for generating match explanation."""
    job_description: str = Field(description="Full job description text")
    resume_content: str = Field(description="Full resume content")
    match_score: float = Field(ge=0, le=100, description="Calculated match score")
    skill_analysis: Dict[str, Any] = Field(description="Skill analysis results")
    include_improvements: bool = Field(default=True, description="Whether to include improvement suggestions")
    format_type: str = Field(default="structured", description="Format type (structured/plain/markdown)")


class ExplanationStats(BaseModel):
    """Statistics about explanation service usage."""
    total_explanations_generated: int = Field(description="Total number of explanations generated")
    llm_explanations: int = Field(description="Number of LLM-generated explanations")
    template_explanations: int = Field(description="Number of template-based explanations")
    cached_explanations: int = Field(description="Number of cached explanations served")
    average_generation_time: float = Field(description="Average time to generate explanation (seconds)")
    cache_hit_rate: float = Field(ge=0, le=100, description="Cache hit rate percentage")


class BatchExplanationRequest(BaseModel):
    """Request for generating multiple explanations."""
    explanations: List[ExplanationRequest] = Field(description="List of explanation requests")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="Maximum concurrent explanations to generate")
    include_stats: bool = Field(default=False, description="Whether to include generation statistics")


class BatchExplanationResponse(BaseModel):
    """Response for batch explanation generation."""
    explanations: List[ExplanationResponse] = Field(description="Generated explanations")
    successful_count: int = Field(description="Number of successfully generated explanations")
    failed_count: int = Field(description="Number of failed explanation generations")
    total_time: float = Field(description="Total time for batch processing (seconds)")
    stats: Optional[ExplanationStats] = Field(default=None, description="Optional generation statistics")