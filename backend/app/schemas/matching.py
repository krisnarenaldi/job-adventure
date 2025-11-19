from __future__ import annotations
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class CandidateStatus(str, Enum):
    """Enum for candidate status in recruitment process"""
    PENDING = "pending"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    MAYBE = "maybe"


class MatchRequest(BaseModel):
    job_id: uuid.UUID
    resume_ids: Optional[List[uuid.UUID]] = None
    include_explanations: bool = True
    min_score_threshold: float = 0.0
    max_results: Optional[int] = None
    
    @field_validator('min_score_threshold')
    def validate_min_score(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError('Min score threshold must be between 0 and 100')
        return v
    
    @field_validator('max_results')
    def validate_max_results(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Max results must be positive')
        return v

    model_config = ConfigDict(from_attributes=True)


class MatchResultBase(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID
    match_score: float
    explanation: str
    key_strengths: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None


class MatchResultCreate(MatchResultBase):
    confidence_score: Optional[float] = None
    skill_matches: Optional[Dict[str, Any]] = None
    experience_score: Optional[float] = None
    skills_score: Optional[float] = None
    education_score: Optional[float] = None
    processing_time_ms: Optional[float] = None
    model_version: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MatchResultInDB(MatchResultBase):
    id: uuid.UUID
    confidence_score: Optional[float] = None
    skill_matches: Optional[Dict[str, Any]] = None
    experience_score: Optional[float] = None
    skills_score: Optional[float] = None
    education_score: Optional[float] = None
    processing_time_ms: Optional[float] = None
    model_version: Optional[str] = None
    status: Optional[CandidateStatus] = CandidateStatus.PENDING
    status_updated_at: Optional[datetime] = None
    status_updated_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MatchResultResponse(MatchResultInDB):
    # Include related objects
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    resume: Optional[Dict[str, Any]] = None  # Include full resume object


class MatchResultListResponse(BaseModel):
    matches: List[MatchResultResponse]
    total: int
    skip: int
    limit: int


class RankingRequest(BaseModel):
    job_id: uuid.UUID
    min_score: Optional[float] = 0.0
    max_results: Optional[int] = 50
    sort_by: str = "match_score"  # match_score, created_at
    sort_order: str = "desc"  # desc, asc
    
    @field_validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ["match_score", "created_at", "confidence_score"]
        if v not in allowed_fields:
            raise ValueError(f'Sort by must be one of: {", ".join(allowed_fields)}')
        return v
    
    @field_validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v
        
    model_config = ConfigDict(from_attributes=True)


class CandidateRanking(BaseModel):
    resume_id: uuid.UUID
    candidate_name: str
    candidate_email: Optional[str] = None
    match_score: float
    confidence_score: Optional[float] = None
    key_strengths: List[str]
    missing_skills: List[str]
    rank: int


class RankingResponse(BaseModel):
    job_id: uuid.UUID
    job_title: str
    job_company: str
    candidates: List[CandidateRanking]
    total_candidates: int
    avg_score: float
    top_score: float


class MatchStatistics(BaseModel):
    job_id: uuid.UUID
    total_candidates: int
    avg_score: float
    top_score: float
    candidates_above_70: int
    candidates_above_50: int
    most_common_missing_skills: List[str]
    score_distribution: Dict[str, int]  # {"high": count, "medium": count, "low": count}


class BatchMatchRequest(BaseModel):
    job_ids: List[uuid.UUID]
    resume_ids: Optional[List[uuid.UUID]] = None
    min_score_threshold: float = 0.0
    
    @field_validator('job_ids')
    def validate_job_ids(cls, v):
        if not v:
            raise ValueError('At least one job ID is required')
        if len(v) > 10:
            raise ValueError('Maximum 10 jobs allowed per batch request')
        return v


class BatchMatchResponse(BaseModel):
    results: Dict[str, MatchResultListResponse]  # job_id -> match results
    total_matches: int
    processing_time_seconds: float


class SimilaritySearchRequest(BaseModel):
    query_text: str
    search_type: str = "jobs"  # "jobs" or "resumes"
    limit: int = 10
    threshold: float = 0.7
    
    @field_validator('search_type')
    def validate_search_type(cls, v):
        if v not in ["jobs", "resumes"]:
            raise ValueError('Search type must be "jobs" or "resumes"')
        return v
    
    @field_validator('limit')
    def validate_limit(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    @field_validator('threshold')
    def validate_threshold(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Threshold must be between 0.0 and 1.0')
        return v
        
    model_config = ConfigDict(from_attributes=True)


class SimilarityResult(BaseModel):
    id: uuid.UUID
    title: str
    content_preview: str
    similarity: float


class SimilaritySearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[SimilarityResult]
    total_found: int


class StatusUpdateRequest(BaseModel):
    """Request schema for updating candidate status"""
    status: CandidateStatus
    
    model_config = ConfigDict(from_attributes=True)


class StatusUpdateResponse(BaseModel):
    """Response schema for status update"""
    id: uuid.UUID
    status: CandidateStatus
    status_updated_at: datetime
    status_updated_by: uuid.UUID
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class StatusHistoryEntry(BaseModel):
    """Single status history entry"""
    status: CandidateStatus
    updated_at: datetime
    updated_by: uuid.UUID
    updated_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class StatusHistoryResponse(BaseModel):
    """Response schema for status history"""
    match_id: uuid.UUID
    current_status: CandidateStatus
    history: List[StatusHistoryEntry]
    
    model_config = ConfigDict(from_attributes=True)