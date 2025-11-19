from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    ApplicantCountResponse,
    MatchScoreMetrics,
    SkillsGapAnalysis,
    JobPerformanceMetrics,
    RecruitmentOverview,
    AnalyticsRequest,
    HistoricalAnalyticsRequest,
    ReportGenerationRequest,
    GeneratedReport,
    ErrorResponse
)

router = APIRouter()


@router.get(
    "/applicant-counts",
    response_model=ApplicantCountResponse,
    summary="Get applicant counts per job",
    description="Retrieve the number of applicants for each job or a specific job"
)
async def get_applicant_counts(
    job_id: Optional[UUID] = Query(None, description="Filter by specific job ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get applicant counts per job
    Requirements: 4.1, 4.4 - Display total number of applicants per job role
    """
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_applicant_count_per_job(job_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ApplicantCountResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve applicant counts: {str(e)}")


@router.get(
    "/match-scores",
    response_model=MatchScoreMetrics,
    summary="Get match score analytics",
    description="Calculate average match scores and score distribution"
)
async def get_match_score_analytics(
    job_id: Optional[UUID] = Query(None, description="Filter by specific job ID"),
    date_range_days: Optional[int] = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get match score analytics
    Requirements: 4.2, 4.4 - Calculate and display average match score across all candidates
    """
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.calculate_average_match_scores(job_id, date_range_days)
        
        return MatchScoreMetrics(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate match scores: {str(e)}")


@router.get(
    "/skills-gap",
    response_model=SkillsGapAnalysis,
    summary="Get skills gap analysis",
    description="Analyze most commonly missing skills across candidates"
)
async def get_skills_gap_analysis(
    job_id: Optional[UUID] = Query(None, description="Filter by specific job ID"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Limit number of skills returned"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skills gap analysis
    Requirements: 4.3, 4.4 - Identify and display most commonly missing skills across candidates
    """
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.analyze_missing_skills(job_id, limit)
        
        return SkillsGapAnalysis(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze skills gap: {str(e)}")


@router.get(
    "/job-performance/{job_id}",
    response_model=JobPerformanceMetrics,
    summary="Get comprehensive job performance metrics",
    description="Get detailed analytics for a specific job including applicants, scores, and skills analysis"
)
async def get_job_performance_metrics(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive job performance metrics
    Requirements: 4.1, 4.2, 4.3, 4.4 - Comprehensive job analytics
    """
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_job_performance_metrics(job_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return JobPerformanceMetrics(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job performance metrics: {str(e)}")


@router.get(
    "/overview",
    response_model=RecruitmentOverview,
    summary="Get recruitment overview",
    description="Get comprehensive recruitment metrics overview with trends"
)
async def get_recruitment_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recruitment overview
    Requirements: 4.4, 4.5 - Maintain historical data for trend analysis over time
    """
    try:
        analytics_service = AnalyticsService(db)
        result = await analytics_service.get_recruitment_overview(days)
        
        return RecruitmentOverview(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recruitment overview: {str(e)}")


@router.post(
    "/historical",
    summary="Get historical analytics data",
    description="Retrieve historical analytics data for specified date range and grouping"
)
async def get_historical_analytics(
    request: HistoricalAnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical analytics data
    Requirements: 4.5 - Maintain historical data for trend analysis over time
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Validate date range
        if request.end_date <= request.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Calculate date range in days
        date_diff = (request.end_date - request.start_date).days
        if date_diff > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # For now, return overview data for the specified period
        # This can be extended to support more granular historical analysis
        result = await analytics_service.get_recruitment_overview(date_diff)
        
        return {
            "period": {
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "days": date_diff,
                "group_by": request.group_by
            },
            "data": result,
            "job_filters": [str(job_id) for job_id in request.job_ids] if request.job_ids else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve historical analytics: {str(e)}")


@router.post(
    "/reports/generate",
    response_model=GeneratedReport,
    summary="Generate analytics report",
    description="Generate comprehensive analytics reports in various formats"
)
async def generate_analytics_report(
    request: ReportGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate analytics report
    Requirements: 6.3 - Allow Hiring_Manager to export candidate rankings and analysis reports
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Validate report type
        valid_report_types = ["summary", "detailed", "skills_gap"]
        if request.report_type not in valid_report_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid report type. Must be one of: {', '.join(valid_report_types)}"
            )
        
        # Generate report data based on type
        if request.report_type == "summary":
            report_data = await analytics_service.get_recruitment_overview(request.date_range_days or 30)
        elif request.report_type == "detailed":
            # Get detailed metrics for all jobs or specified jobs
            if request.job_ids:
                report_data = {}
                for job_id in request.job_ids:
                    job_metrics = await analytics_service.get_job_performance_metrics(job_id)
                    if "error" not in job_metrics:
                        report_data[str(job_id)] = job_metrics
            else:
                report_data = await analytics_service.get_recruitment_overview(request.date_range_days or 30)
        elif request.report_type == "skills_gap":
            # Generate skills gap report
            if request.job_ids and len(request.job_ids) == 1:
                report_data = await analytics_service.analyze_missing_skills(request.job_ids[0])
            else:
                report_data = await analytics_service.analyze_missing_skills()
        
        # Generate report ID and metadata
        report_id = f"report_{request.report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            "report_type": request.report_type,
            "generated_by": str(current_user.id),
            "job_filters": [str(job_id) for job_id in request.job_ids] if request.job_ids else None,
            "date_range_days": request.date_range_days,
            "include_candidates": request.include_candidates,
            "format": request.format
        }
        
        return GeneratedReport(
            report_id=report_id,
            report_type=request.report_type,
            generated_at=datetime.utcnow().isoformat(),
            data=report_data,
            metadata=metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get(
    "/health",
    summary="Analytics service health check",
    description="Check if analytics service is operational"
)
async def analytics_health_check(
    db: AsyncSession = Depends(get_db)
):
    """Health check for analytics service"""
    try:
        analytics_service = AnalyticsService(db)
        
        # Simple test query to verify database connectivity
        overview = await analytics_service.get_recruitment_overview(1)
        
        return {
            "status": "healthy",
            "service": "analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "database_connected": True
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "database_connected": False
        }