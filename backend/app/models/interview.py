from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
import enum


class InterviewType(str, enum.Enum):
    """Enum for interview types"""
    PHONE = "phone"
    VIDEO = "video"
    IN_PERSON = "in-person"


class InterviewStatus(str, enum.Enum):
    """Enum for interview status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    match_result_id = Column(PostgresUUID(as_uuid=True), ForeignKey("match_results.id"), nullable=False, index=True)
    job_id = Column(PostgresUUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    
    # Interview details
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)    
    interview_type = Column(Enum(InterviewType, name="interviewtype", native_enum=True, values_callable=lambda x: [e.value for e in x]), nullable=False, default=InterviewType.VIDEO)
    status = Column(Enum(InterviewStatus, name="interviewstatus", native_enum=True, values_callable=lambda x: [e.value for e in x]), nullable=False, default=InterviewStatus.SCHEDULED, index=True)
    
    # Meeting details
    meeting_link = Column(String(500), nullable=True)
    location = Column(String(500), nullable=True)  # For in-person interviews
    notes = Column(Text, nullable=True)
    
    # Email tracking
    invitation_sent = Column(DateTime(timezone=True), nullable=True)
    invitation_opened = Column(DateTime(timezone=True), nullable=True)
    invitation_clicked = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    match_result = relationship("MatchResult", backref="interviews")
    job = relationship("JobDescription", backref="interviews")
    creator = relationship("User", foreign_keys=[created_by], backref="created_interviews")
    canceller = relationship("User", foreign_keys=[cancelled_by], backref="cancelled_interviews")
    
    def __repr__(self):
        return f"<Interview(id={self.id}, job_id={self.job_id}, scheduled_time={self.scheduled_time}, status={self.status})>"


# Create indexes for performance
Index('idx_interview_match_result', Interview.match_result_id)
Index('idx_interview_job', Interview.job_id)
Index('idx_interview_scheduled_time', Interview.scheduled_time)
Index('idx_interview_status', Interview.status)
Index('idx_interview_created_by', Interview.created_by)
Index('idx_interview_job_status', Interview.job_id, Interview.status)
