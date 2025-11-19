from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.interview import InterviewType, InterviewStatus


class InterviewBase(BaseModel):
    scheduled_time: datetime
    interview_type: InterviewType
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class InterviewCreate(InterviewBase):
    match_result_id: UUID
    job_id: UUID


class InterviewUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    interview_type: Optional[InterviewType] = None
    status: Optional[InterviewStatus] = None
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class InterviewResponse(InterviewBase):
    id: UUID
    match_result_id: UUID
    job_id: UUID
    status: InterviewStatus
    invitation_sent: Optional[datetime] = None
    invitation_opened: Optional[datetime] = None
    invitation_clicked: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[UUID] = None

    class Config:
        from_attributes = True
