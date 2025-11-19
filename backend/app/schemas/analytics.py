from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID


class JobApplicantCount(BaseModel):
    """Schema for job applicant count data"""
    job_id: str
    job_title: str
    company: str
    applicant_count: int


class ApplicantCountResponse(BaseModel):
    """Response schema for applicant count metrics"""
    total_jobs: Optional[int] = None
    jobs: Optional[List[JobApplicantCount]] = None
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    applicant_count: Optional[int] = None


class ScoreDistribution(BaseModel):
    """Schema for match score distribution"""
    excellent: int = Field(..., description="Scores 80-100%")
    good: int = Field(..., description="Scores 60-79%")
    fair: int = Field(..., description="Scores 40-59%")
    poor: int = Field(..., description="Scores 0-39%")


class MatchScoreMetrics(BaseModel):
    """Schema for match score analysis"""
    average_score: float
    total_matches: int
    min_score: float
    max_score: float
    standard_deviation: float
    score_distribution: ScoreDistribution


class MissingSkill(BaseModel):
    """Schema for missing skill data"""
    skill: str
    missing_count: int
    percentage_missing: float


class SkillsAnalysisMetadata(BaseModel):
    """Metadata for skills analysis"""
    unique_missing_skills: int
    total_skill_gaps: int


class SkillsGapAnalysis(BaseModel):
    """Schema for skills gap analysis"""
    total_candidates_analyzed: int
    most_missing_skills: List[MissingSkill]
    skills_gap_summary: str
    analysis_metadata: SkillsAnalysisMetadata


class TopCandidate(BaseModel):
    """Schema for top candidate data"""
    resume_id: str
    candidate_name: str
    match_score: float
    key_strengths: List[str]


class JobInfo(BaseModel):
    """Schema for job information"""
    job_id: str
    title: str
    company: str
    created_at: Optional[str] = None


class JobPerformanceMetrics(BaseModel):
    """Schema for comprehensive job performance metrics"""
    job_info: JobInfo
    applicant_metrics: ApplicantCountResponse
    score_metrics: MatchScoreMetrics
    skills_analysis: SkillsGapAnalysis
    top_candidates: List[TopCandidate]


class RecruitmentSummary(BaseModel):
    """Schema for recruitment summary data"""
    total_jobs: int
    total_resumes: int
    total_matches: int


class ActivityTrend(BaseModel):
    """Schema for daily activity trend"""
    date: Optional[str] = None
    matches_count: int


class RecruitmentOverview(BaseModel):
    """Schema for overall recruitment metrics"""
    period_days: int
    summary: RecruitmentSummary
    job_metrics: ApplicantCountResponse
    score_analysis: MatchScoreMetrics
    skills_gap_analysis: SkillsGapAnalysis
    activity_trend: List[ActivityTrend]
    generated_at: str


class AnalyticsRequest(BaseModel):
    """Base request schema for analytics endpoints"""
    job_id: Optional[UUID] = Field(None, description="Filter by specific job ID")
    date_range_days: Optional[int] = Field(30, ge=1, le=365, description="Number of days to analyze")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Limit for results")


class HistoricalAnalyticsRequest(BaseModel):
    """Request schema for historical analytics"""
    start_date: datetime = Field(..., description="Start date for analysis")
    end_date: datetime = Field(..., description="End date for analysis")
    job_ids: Optional[List[UUID]] = Field(None, description="Filter by specific job IDs")
    group_by: Optional[str] = Field("day", description="Grouping period: day, week, month")


class ReportGenerationRequest(BaseModel):
    """Request schema for report generation"""
    report_type: str = Field(..., description="Type of report: summary, detailed, skills_gap")
    job_ids: Optional[List[UUID]] = Field(None, description="Filter by specific job IDs")
    date_range_days: Optional[int] = Field(30, description="Number of days to include")
    include_candidates: bool = Field(False, description="Include candidate details in report")
    format: str = Field("json", description="Report format: json, csv")


class GeneratedReport(BaseModel):
    """Schema for generated report response"""
    report_id: str
    report_type: str
    generated_at: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    details: Optional[str] = None