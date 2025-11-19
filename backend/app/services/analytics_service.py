from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from sqlalchemy.orm import selectinload
from app.models.match_result import MatchResult
from app.models.job import JobDescription
from app.models.resume import Resume
from app.repositories.match_result import MatchResultRepository
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeRepository
import uuid
from collections import Counter


class AnalyticsService:
    """Service for calculating recruitment analytics and metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.match_repo = MatchResultRepository(db)
        self.job_repo = JobRepository(db)
        self.resume_repo = ResumeRepository(db)
    
    async def get_applicant_count_per_job(self, job_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """
        Calculate applicant counts per job
        Requirements: 4.1 - Display total number of applicants per job role
        """
        if job_id:
            # Get count for specific job
            result = await self.db.execute(
                select(func.count(MatchResult.id))
                .where(MatchResult.job_id == job_id)
            )
            count = result.scalar() or 0
            
            # Get job details
            job = await self.job_repo.get(job_id)
            if not job:
                return {"error": "Job not found"}
            
            return {
                "job_id": str(job_id),
                "job_title": job.title,
                "company": job.company,
                "applicant_count": count
            }
        else:
            # Get counts for all jobs
            result = await self.db.execute(
                select(
                    JobDescription.id,
                    JobDescription.title,
                    JobDescription.company,
                    func.count(MatchResult.id).label('applicant_count')
                )
                .outerjoin(MatchResult, JobDescription.id == MatchResult.job_id)
                .group_by(JobDescription.id, JobDescription.title, JobDescription.company)
                .order_by(desc('applicant_count'))
            )
            
            jobs_data = []
            for row in result:
                jobs_data.append({
                    "job_id": str(row.id),
                    "job_title": row.title,
                    "company": row.company,
                    "applicant_count": row.applicant_count or 0
                })
            
            return {
                "total_jobs": len(jobs_data),
                "jobs": jobs_data
            }
    
    async def calculate_average_match_scores(
        self, 
        job_id: Optional[uuid.UUID] = None,
        date_range_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate average match scores across candidates
        Requirements: 4.2 - Calculate and display average match score across all candidates
        """
        query = select(
            func.avg(MatchResult.match_score).label('avg_score'),
            func.count(MatchResult.id).label('total_matches'),
            func.min(MatchResult.match_score).label('min_score'),
            func.max(MatchResult.match_score).label('max_score'),
            func.stddev(MatchResult.match_score).label('std_dev')
        )
        
        # Apply filters
        conditions = []
        if job_id:
            conditions.append(MatchResult.job_id == job_id)
        
        if date_range_days:
            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
            conditions.append(MatchResult.created_at >= cutoff_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row or row.total_matches == 0:
            return {
                "average_score": 0.0,
                "total_matches": 0,
                "min_score": 0.0,
                "max_score": 0.0,
                "standard_deviation": 0.0
            }
        
        # Calculate score distribution
        distribution_query = select(
            func.count(MatchResult.id).filter(MatchResult.match_score >= 80).label('excellent'),
            func.count(MatchResult.id).filter(
                and_(MatchResult.match_score >= 60, MatchResult.match_score < 80)
            ).label('good'),
            func.count(MatchResult.id).filter(
                and_(MatchResult.match_score >= 40, MatchResult.match_score < 60)
            ).label('fair'),
            func.count(MatchResult.id).filter(MatchResult.match_score < 40).label('poor')
        )
        
        if conditions:
            distribution_query = distribution_query.where(and_(*conditions))
        
        dist_result = await self.db.execute(distribution_query)
        dist_row = dist_result.first()
        
        return {
            "average_score": float(row.avg_score or 0.0),
            "total_matches": row.total_matches,
            "min_score": float(row.min_score or 0.0),
            "max_score": float(row.max_score or 0.0),
            "standard_deviation": float(row.std_dev or 0.0),
            "score_distribution": {
                "excellent": dist_row.excellent or 0,  # 80-100%
                "good": dist_row.good or 0,           # 60-79%
                "fair": dist_row.fair or 0,           # 40-59%
                "poor": dist_row.poor or 0            # 0-39%
            }
        }
    
    async def analyze_missing_skills(
        self, 
        job_id: Optional[uuid.UUID] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze most commonly missing skills across candidates
        Requirements: 4.3 - Identify and display most commonly missing skills across candidates
        """
        query = select(MatchResult.missing_skills)
        
        if job_id:
            query = query.where(MatchResult.job_id == job_id)
        
        result = await self.db.execute(query)
        all_missing_skills = []
        
        for row in result:
            if row.missing_skills:
                all_missing_skills.extend(row.missing_skills)
        
        if not all_missing_skills:
            return {
                "total_candidates_analyzed": 0,
                "most_missing_skills": [],
                "skills_gap_summary": "No missing skills data available"
            }
        
        # Count skill frequencies
        skill_counter = Counter(all_missing_skills)
        most_common_skills = skill_counter.most_common(limit)
        
        # Calculate total candidates analyzed
        total_candidates_result = await self.db.execute(
            select(func.count(MatchResult.id))
            .where(MatchResult.job_id == job_id if job_id else True)
        )
        total_candidates = total_candidates_result.scalar() or 0
        
        # Format results
        missing_skills_data = []
        for skill, count in most_common_skills:
            percentage = (count / total_candidates * 100) if total_candidates > 0 else 0
            missing_skills_data.append({
                "skill": skill,
                "missing_count": count,
                "percentage_missing": round(percentage, 2)
            })
        
        # Generate summary
        top_3_skills = [item["skill"] for item in missing_skills_data[:3]]
        summary = f"Top missing skills: {', '.join(top_3_skills)}" if top_3_skills else "No significant skill gaps identified"
        
        return {
            "total_candidates_analyzed": total_candidates,
            "most_missing_skills": missing_skills_data,
            "skills_gap_summary": summary,
            "analysis_metadata": {
                "unique_missing_skills": len(skill_counter),
                "total_skill_gaps": sum(skill_counter.values())
            }
        }
    
    async def get_job_performance_metrics(self, job_id: uuid.UUID) -> Dict[str, Any]:
        """Get comprehensive performance metrics for a specific job"""
        # Get basic job info
        job = await self.job_repo.get(job_id)
        if not job:
            return {"error": "Job not found"}
        
        # Get applicant count
        applicant_data = await self.get_applicant_count_per_job(job_id)
        
        # Get average scores
        score_data = await self.calculate_average_match_scores(job_id)
        
        # Get missing skills analysis
        skills_data = await self.analyze_missing_skills(job_id)
        
        # Get top candidates
        top_matches = await self.match_repo.get_top_matches_for_job(job_id, limit=5)
        top_candidates = []
        for match in top_matches:
            top_candidates.append({
                "resume_id": str(match.resume_id),
                "candidate_name": match.resume.candidate_name if match.resume else "Unknown",
                "match_score": float(match.match_score),
                "key_strengths": match.key_strengths or []
            })
        
        return {
            "job_info": {
                "job_id": str(job.id),
                "title": job.title,
                "company": job.company,
                "created_at": job.created_at.isoformat() if job.created_at else None
            },
            "applicant_metrics": applicant_data,
            "score_metrics": score_data,
            "skills_analysis": skills_data,
            "top_candidates": top_candidates
        }
    
    async def get_recruitment_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get overall recruitment metrics overview"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total jobs and resumes
        total_jobs_result = await self.db.execute(
            select(func.count(JobDescription.id))
            .where(JobDescription.created_at >= cutoff_date)
        )
        total_jobs = total_jobs_result.scalar() or 0
        
        total_resumes_result = await self.db.execute(
            select(func.count(Resume.id))
            .where(Resume.uploaded_at >= cutoff_date)
        )
        total_resumes = total_resumes_result.scalar() or 0
        
        # Get overall metrics
        applicant_data = await self.get_applicant_count_per_job()
        score_data = await self.calculate_average_match_scores(date_range_days=days)
        skills_data = await self.analyze_missing_skills()
        
        # Activity trends (last 7 days)
        activity_result = await self.db.execute(
            select(
                func.date(MatchResult.created_at).label('date'),
                func.count(MatchResult.id).label('matches_count')
            )
            .where(MatchResult.created_at >= datetime.utcnow() - timedelta(days=7))
            .group_by(func.date(MatchResult.created_at))
            .order_by('date')
        )
        
        activity_trend = []
        for row in activity_result:
            activity_trend.append({
                "date": row.date.isoformat() if row.date else None,
                "matches_count": row.matches_count
            })
        
        return {
            "period_days": days,
            "summary": {
                "total_jobs": total_jobs,
                "total_resumes": total_resumes,
                "total_matches": score_data["total_matches"]
            },
            "job_metrics": applicant_data,
            "score_analysis": score_data,
            "skills_gap_analysis": skills_data,
            "activity_trend": activity_trend,
            "generated_at": datetime.utcnow().isoformat()
        }