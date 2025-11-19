from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.shared_link import SharedLink
from app.repositories.base import BaseRepository
import uuid
import secrets
from datetime import datetime


class SharedLinkRepository(BaseRepository[SharedLink]):
    """Repository for SharedLink model operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(SharedLink, db)
    
    async def get_by_token(self, token: str) -> Optional[SharedLink]:
        """Get shared link by token"""
        result = await self.db.execute(
            select(SharedLink).where(SharedLink.share_token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_by_job(self, job_id: uuid.UUID) -> List[SharedLink]:
        """Get all shared links for a job"""
        result = await self.db.execute(
            select(SharedLink)
            .where(SharedLink.job_id == job_id)
            .order_by(SharedLink.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_active_by_job(self, job_id: uuid.UUID) -> List[SharedLink]:
        """Get active (non-expired) shared links for a job"""
        result = await self.db.execute(
            select(SharedLink)
            .where(
                and_(
                    SharedLink.job_id == job_id,
                    SharedLink.is_active == True
                )
            )
            .order_by(SharedLink.created_at.desc())
        )
        links = result.scalars().all()
        # Filter out expired links
        return [link for link in links if link.is_valid()]
    
    async def create_shared_link(
        self,
        job_id: uuid.UUID,
        created_by: uuid.UUID,
        recipient_email: Optional[str] = None,
        custom_message: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> SharedLink:
        """Create a new shared link"""
        # Generate unique token
        share_token = secrets.token_urlsafe(32)
        
        shared_link = SharedLink(
            job_id=job_id,
            share_token=share_token,
            created_by=created_by,
            recipient_email=recipient_email,
            custom_message=custom_message,
            expires_at=expires_at
        )
        
        self.db.add(shared_link)
        await self.db.commit()
        await self.db.refresh(shared_link)
        
        return shared_link
    
    async def increment_view_count(self, link_id: uuid.UUID) -> Optional[SharedLink]:
        """Increment view count and update last viewed timestamp"""
        link = await self.get(link_id)
        if link:
            link.view_count += 1
            link.last_viewed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(link)
        return link
    
    async def deactivate_link(self, link_id: uuid.UUID) -> Optional[SharedLink]:
        """Deactivate a shared link"""
        link = await self.get(link_id)
        if link:
            link.is_active = False
            await self.db.commit()
            await self.db.refresh(link)
        return link
    
    async def get_by_creator(self, creator_id: uuid.UUID) -> List[SharedLink]:
        """Get all shared links created by a user"""
        result = await self.db.execute(
            select(SharedLink)
            .where(SharedLink.created_by == creator_id)
            .order_by(SharedLink.created_at.desc())
        )
        return result.scalars().all()
