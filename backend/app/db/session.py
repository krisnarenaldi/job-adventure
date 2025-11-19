from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal, get_db
from app.repositories import (
    UserRepository,
    JobRepository,
    ResumeRepository,
    MatchResultRepository
)


class DatabaseSession:
    """Database session manager with repository access"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._user_repo = None
        self._job_repo = None
        self._resume_repo = None
        self._match_result_repo = None
    
    @property
    def users(self) -> UserRepository:
        """Get user repository"""
        if self._user_repo is None:
            self._user_repo = UserRepository(self.db)
        return self._user_repo
    
    @property
    def jobs(self) -> JobRepository:
        """Get job repository"""
        if self._job_repo is None:
            self._job_repo = JobRepository(self.db)
        return self._job_repo
    
    @property
    def resumes(self) -> ResumeRepository:
        """Get resume repository"""
        if self._resume_repo is None:
            self._resume_repo = ResumeRepository(self.db)
        return self._resume_repo
    
    @property
    def match_results(self) -> MatchResultRepository:
        """Get match result repository"""
        if self._match_result_repo is None:
            self._match_result_repo = MatchResultRepository(self.db)
        return self._match_result_repo
    
    async def commit(self):
        """Commit the current transaction"""
        await self.db.commit()
    
    async def rollback(self):
        """Rollback the current transaction"""
        await self.db.rollback()
    
    async def close(self):
        """Close the database session"""
        await self.db.close()


async def get_db_session() -> DatabaseSession:
    """Dependency to get database session with repositories"""
    async with AsyncSessionLocal() as session:
        try:
            yield DatabaseSession(session)
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()