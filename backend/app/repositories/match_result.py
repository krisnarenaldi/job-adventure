from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.models.match_result import MatchResult
from app.repositories.base import BaseRepository
import uuid


class MatchResultRepository(BaseRepository[MatchResult]):
    """Repository for MatchResult model operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(MatchResult, db)
    
    async def get_by_job(self, job_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[MatchResult]:
        """Get all match results for a specific job"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.resume))
            .where(MatchResult.job_id == job_id)
            .order_by(desc(MatchResult.match_score))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_resume(self, resume_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[MatchResult]:
        """Get all match results for a specific resume"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.job))
            .where(MatchResult.resume_id == resume_id)
            .order_by(desc(MatchResult.match_score))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_match(self, job_id: uuid.UUID, resume_id: uuid.UUID) -> Optional[MatchResult]:
        """Get specific match result between a job and resume"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.job), selectinload(MatchResult.resume))
            .where(MatchResult.job_id == job_id)
            .where(MatchResult.resume_id == resume_id)
        )
        return result.scalar_one_or_none()
    
    async def get_top_matches_for_job(
        self, 
        job_id: uuid.UUID, 
        min_score: float = 0.0,
        limit: int = 10
    ) -> List[MatchResult]:
        """Get top matching resumes for a job"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.resume))
            .where(MatchResult.job_id == job_id)
            .where(MatchResult.match_score >= min_score)
            .order_by(desc(MatchResult.match_score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_top_matches_for_resume(
        self, 
        resume_id: uuid.UUID, 
        min_score: float = 0.0,
        limit: int = 10
    ) -> List[MatchResult]:
        """Get top matching jobs for a resume"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.job))
            .where(MatchResult.resume_id == resume_id)
            .where(MatchResult.match_score >= min_score)
            .order_by(desc(MatchResult.match_score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_matches_by_score_range(
        self, 
        min_score: float, 
        max_score: float,
        skip: int = 0, 
        limit: int = 100
    ) -> List[MatchResult]:
        """Get matches within a specific score range"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.job), selectinload(MatchResult.resume))
            .where(MatchResult.match_score >= min_score)
            .where(MatchResult.match_score <= max_score)
            .order_by(desc(MatchResult.match_score))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent_matches(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[MatchResult]:
        """Get recent matches within specified days"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.job), selectinload(MatchResult.resume))
            .where(MatchResult.created_at >= func.now() - func.interval(f'{days} days'))
            .order_by(desc(MatchResult.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_matches_by_creator(
        self, 
        creator_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[MatchResult]:
        """Get matches created by a specific user"""
        result = await self.db.execute(
            select(MatchResult)
            .options(selectinload(MatchResult.job), selectinload(MatchResult.resume))
            .where(MatchResult.created_by == creator_id)
            .order_by(desc(MatchResult.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_match_statistics(self) -> Dict[str, Any]:
        """Get overall matching statistics"""
        # Total matches
        total_result = await self.db.execute(select(func.count(MatchResult.id)))
        total_matches = total_result.scalar()
        
        # Average score
        avg_result = await self.db.execute(select(func.avg(MatchResult.match_score)))
        avg_score = avg_result.scalar() or 0.0
        
        # Score distribution
        high_score_result = await self.db.execute(
            select(func.count(MatchResult.id)).where(MatchResult.match_score >= 80.0)
        )
        medium_score_result = await self.db.execute(
            select(func.count(MatchResult.id))
            .where(MatchResult.match_score >= 60.0)
            .where(MatchResult.match_score < 80.0)
        )
        low_score_result = await self.db.execute(
            select(func.count(MatchResult.id)).where(MatchResult.match_score < 60.0)
        )
        
        return {
            "total_matches": total_matches,
            "average_score": float(avg_score),
            "high_score_matches": high_score_result.scalar(),  # >= 80%
            "medium_score_matches": medium_score_result.scalar(),  # 60-79%
            "low_score_matches": low_score_result.scalar()  # < 60%
        }
    
    async def delete_matches_for_job(self, job_id: uuid.UUID) -> int:
        """Delete all matches for a specific job"""
        result = await self.db.execute(
            select(func.count(MatchResult.id)).where(MatchResult.job_id == job_id)
        )
        count = result.scalar()
        
        await self.db.execute(
            select(MatchResult).where(MatchResult.job_id == job_id)
        )
        await self.db.commit()
        
        return count
    
    async def delete_matches_for_resume(self, resume_id: uuid.UUID) -> int:
        """Delete all matches for a specific resume"""
        result = await self.db.execute(
            select(func.count(MatchResult.id)).where(MatchResult.resume_id == resume_id)
        )
        count = result.scalar()
        
        await self.db.execute(
            select(MatchResult).where(MatchResult.resume_id == resume_id)
        )
        await self.db.commit()
        
        return count
    
    # Commented out until migration is applied
    # async def update_status(
    #     self, 
    #     match_id: uuid.UUID, 
    #     status: str, 
    #     updated_by: uuid.UUID
    # ) -> Optional[MatchResult]:
    #     """Update the status of a match result"""
    #     pass
    
    # async def get_by_status(
    #     self, 
    #     job_id: uuid.UUID, 
    #     status: str, 
    #     skip: int = 0, 
    #     limit: int = 100
    # ) -> List[MatchResult]:
    #     """Get match results filtered by status"""
    #     pass