from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.models.job import JobDescription
from app.repositories.base import BaseRepository
import uuid


class JobRepository(BaseRepository[JobDescription]):
    """Repository for JobDescription model operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(JobDescription, db)
    
    async def get_by_creator(self, creator_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get jobs created by a specific user"""
        # Get all jobs by creator (both active and inactive)
        query = select(JobDescription).where(
            JobDescription.created_by == creator_id
        )
        
        # Add ordering and pagination
        query = query.order_by(JobDescription.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_company_id(self, company_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get jobs for all users in the same company (team collaboration)"""
        from app.models.user import User
        
        # Join with users table to filter by company_id
        query = select(JobDescription).join(
            User, JobDescription.created_by == User.id
        ).where(
            User.company_id == company_id
        )
        
        # Add ordering and pagination
        query = query.order_by(JobDescription.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_company(self, company: str, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get jobs by company name"""
        result = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.company.ilike(f"%{company}%"))
            .where(JobDescription.is_active == True)
            .order_by(JobDescription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_by_title(self, title: str, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Search jobs by title"""
        result = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.title.ilike(f"%{title}%"))
            .where(JobDescription.is_active == True)
            .order_by(JobDescription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_jobs_optimized(self, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get active jobs with optimized query using index"""
        result = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.is_active == True)
            .order_by(JobDescription.created_at.desc())
            .offset(skip)
            .limit(limit)
            .execution_options(compiled_cache={})  # Use prepared statement cache
        )
        return result.scalars().all()
    
    async def get_jobs_with_embeddings(self, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get jobs that have embeddings generated"""
        result = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.embedding.is_not(None))
            .where(JobDescription.is_active == True)
            .order_by(JobDescription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def bulk_update_embeddings(self, job_embeddings: List[Dict[str, Any]]) -> bool:
        """Bulk update embeddings for multiple jobs"""
        try:
            for job_data in job_embeddings:
                await self.db.execute(
                    text("UPDATE job_descriptions SET embedding = :embedding WHERE id = :job_id"),
                    {"embedding": job_data["embedding"], "job_id": job_data["job_id"]}
                )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def get_by_skills(self, skills: List[str], skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get jobs that require any of the specified skills"""
        result = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.skills_required.overlap(skills))
            .where(JobDescription.is_active == True)
            .order_by(JobDescription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_jobs(self, skip: int = 0, limit: int = 100) -> List[JobDescription]:
        """Get all active job descriptions"""
        result = await self.db.execute(
            select(JobDescription)
            .where(JobDescription.is_active == True)
            .order_by(JobDescription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find similar jobs using vector similarity search"""
        query = text("""
            SELECT id, title, company, description, 
                   1 - (embedding <=> :query_embedding) as similarity
            FROM job_descriptions 
            WHERE embedding IS NOT NULL 
              AND is_active = true
              AND 1 - (embedding <=> :query_embedding) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(
            query, 
            {
                "query_embedding": str(query_embedding), 
                "threshold": threshold, 
                "limit": limit
            }
        )
        
        return [
            {
                "id": row.id,
                "title": row.title,
                "company": row.company,
                "description": row.description,
                "similarity": float(row.similarity)
            }
            for row in result
        ]
    
    async def update_embedding(self, job_id: uuid.UUID, embedding: List[float]) -> bool:
        """Update job embedding"""
        return await self.update(job_id, {"embedding": embedding}) is not None
    
    async def deactivate_job(self, job_id: uuid.UUID) -> bool:
        """Deactivate a job (soft delete)"""
        return await self.update(job_id, {"is_active": False}) is not None
    
    async def activate_job(self, job_id: uuid.UUID) -> bool:
        """Activate a job"""
        return await self.update(job_id, {"is_active": True}) is not None