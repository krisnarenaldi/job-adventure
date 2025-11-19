from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.models.resume import Resume
from app.repositories.base import BaseRepository
import uuid


class ResumeRepository(BaseRepository[Resume]):
    """Repository for Resume model operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Resume, db)
    
    async def get_by_email(self, email: str) -> Optional[Resume]:
        """Get resume by candidate email"""
        result = await self.db.execute(
            select(Resume).where(Resume.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_candidate_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Search resumes by candidate name"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.candidate_name.ilike(f"%{name}%"))
            .order_by(Resume.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_skills(self, skills: List[str], skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get resumes that have any of the specified skills"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.extracted_skills.overlap(skills))
            .where(Resume.is_processed == "true")
            .order_by(Resume.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_processed_resumes(self, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get all processed resumes"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.is_processed == "true")
            .order_by(Resume.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_unprocessed_resumes(self, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get all unprocessed resumes"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.is_processed == "false")
            .order_by(Resume.uploaded_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_uploaded_by(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get resumes uploaded by a specific user"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.uploaded_by == user_id)
            .order_by(Resume.uploaded_at.desc())
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
        """Find similar resumes using vector similarity search"""
        query = text("""
            SELECT id, candidate_name, email, content,
                   1 - (embedding <=> :query_embedding) as similarity
            FROM resumes 
            WHERE embedding IS NOT NULL 
              AND is_processed = 'true'
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
        
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_processed_resumes_optimized(self, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get processed resumes with optimized query using index"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.is_processed == "true")
            .order_by(Resume.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
            .execution_options(compiled_cache={})  # Use prepared statement cache
        )
        return result.scalars().all()
    
    async def get_resumes_with_embeddings(self, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get resumes that have embeddings generated"""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.embedding.is_not(None))
            .where(Resume.is_processed == "true")
            .order_by(Resume.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def bulk_update_embeddings(self, resume_embeddings: List[Dict[str, Any]]) -> bool:
        """Bulk update embeddings for multiple resumes"""
        try:
            for resume_data in resume_embeddings:
                await self.db.execute(
                    text("UPDATE resumes SET embedding = :embedding WHERE id = :resume_id"),
                    {"embedding": resume_data["embedding"], "resume_id": resume_data["resume_id"]}
                )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def get_resume_stats(self) -> Dict[str, Any]:
        """Get resume statistics for performance monitoring"""
        result = await self.db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_resumes,
                    COUNT(CASE WHEN is_processed = 'true' THEN 1 END) as processed_resumes,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as resumes_with_embeddings,
                    AVG(CASE WHEN processed_at IS NOT NULL AND uploaded_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (processed_at - uploaded_at)) END) as avg_processing_time_seconds
                FROM resumes
            """)
        )
        
        row = result.fetchone()
        return {
            "total_resumes": row[0] or 0,
            "processed_resumes": row[1] or 0,
            "resumes_with_embeddings": row[2] or 0,
            "avg_processing_time_seconds": float(row[3]) if row[3] else 0.0
        } 
    
    async def update_embedding(self, resume_id: uuid.UUID, embedding: List[float]) -> bool:
        """Update resume embedding"""
        return await self.update(resume_id, {"embedding": embedding}) is not None
    
    async def mark_as_processed(self, resume_id: uuid.UUID, processed_data: Dict[str, Any]) -> bool:
        """Mark resume as processed and update extracted data"""
        update_data = {
            "is_processed": "true",
            "processed_at": func.now(),
            **processed_data
        }
        return await self.update(resume_id, update_data) is not None
    
    async def get_resume_stats(self) -> Dict[str, int]:
        """Get resume processing statistics"""
        total_result = await self.db.execute(select(func.count(Resume.id)))
        processed_result = await self.db.execute(
            select(func.count(Resume.id)).where(Resume.is_processed == "true")
        )
        
        total = total_result.scalar()
        processed = processed_result.scalar()
        
        return {
            "total": total,
            "processed": processed,
            "unprocessed": total - processed
        }