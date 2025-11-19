from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.interview import Interview, InterviewStatus
from app.schemas.interview import InterviewCreate, InterviewUpdate


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, interview_data: InterviewCreate, created_by: UUID) -> Interview:
        """Create a new interview"""
        # Use mode='json' to ensure enums are serialized to their values
        # data_dict = interview_data.model_dump(mode='json')
        data_dict = interview_data.model_dump(mode='python')

        interview = Interview(
            **data_dict,
            created_by=created_by
        )

        self.db.add(interview)
        await self.db.flush()  # Flush to get the ID and defaults
        await self.db.refresh(interview)  # Refresh to load server defaults
        await self.db.commit()  # Commit the transaction

        # Access all attributes to ensure they're loaded
        _ = (interview.id, interview.status, interview.created_at, interview.updated_at)

        return interview

    async def get_by_id(self, interview_id: UUID) -> Optional[Interview]:
        """Get interview by ID"""
        result = await self.db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: UUID, status: Optional[InterviewStatus] = None) -> List[Interview]:
        """Get all interviews for a job, optionally filtered by status"""
        query = select(Interview).where(Interview.job_id == job_id)
        if status:
            query = query.where(Interview.status == status)
        query = query.order_by(Interview.scheduled_time)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_match_result_id(self, match_result_id: UUID) -> List[Interview]:
        """Get all interviews for a match result"""
        result = await self.db.execute(
            select(Interview)
            .where(Interview.match_result_id == match_result_id)
            .order_by(Interview.scheduled_time)
        )
        return result.scalars().all()

    async def update(self, interview_id: UUID, interview_data: InterviewUpdate) -> Optional[Interview]:
        """Update an interview"""
        interview = await self.get_by_id(interview_id)
        if not interview:
            return None

        update_data = interview_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interview, field, value)

        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def cancel(self, interview_id: UUID, cancelled_by: UUID) -> Optional[Interview]:
        """Cancel an interview"""
        interview = await self.get_by_id(interview_id)
        if not interview:
            return None

        interview.status = InterviewStatus.CANCELLED
        interview.cancelled_at = datetime.utcnow()
        interview.cancelled_by = cancelled_by

        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def delete(self, interview_id: UUID) -> bool:
        """Delete an interview"""
        interview = await self.get_by_id(interview_id)
        if not interview:
            return False

        self.db.delete(interview)
        await self.db.commit()
        return True

    async def mark_invitation_sent(self, interview_id: UUID) -> Optional[Interview]:
        """Mark invitation as sent"""
        interview = await self.get_by_id(interview_id)
        if not interview:
            return None

        interview.invitation_sent = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def mark_invitation_opened(self, interview_id: UUID) -> Optional[Interview]:
        """Mark invitation as opened"""
        interview = await self.get_by_id(interview_id)
        if not interview:
            return None

        interview.invitation_opened = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def mark_invitation_clicked(self, interview_id: UUID) -> Optional[Interview]:
        """Mark invitation link as clicked"""
        interview = await self.get_by_id(interview_id)
        if not interview:
            return None

        interview.invitation_clicked = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(interview)
        return interview
