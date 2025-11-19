from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Index, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
import enum


class CandidateStatus(str, enum.Enum):
    """Enum for candidate status in recruitment process"""
    PENDING = "pending"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    MAYBE = "maybe"


class MatchResult(Base):
    __tablename__ = "match_results"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    job_id = Column(PostgresUUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    resume_id = Column(PostgresUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    
    # Match scoring
    match_score = Column(Numeric(5, 2), nullable=False, index=True)  # 0.00 to 100.00
    confidence_score = Column(Numeric(5, 2), nullable=True)  # AI confidence in the match
    
    # Detailed analysis
    explanation = Column(Text, nullable=False)
    key_strengths = Column(ARRAY(String), nullable=True)
    missing_skills = Column(ARRAY(String), nullable=True)
    skill_matches = Column(JSON, nullable=True)  # {"matched": [...], "missing": [...], "additional": [...]}
    
    # Section-wise scores
    experience_score = Column(Numeric(5, 2), nullable=True)
    skills_score = Column(Numeric(5, 2), nullable=True)
    education_score = Column(Numeric(5, 2), nullable=True)
    
    # Candidate status management
    status = Column(Enum(CandidateStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=CandidateStatus.PENDING, server_default='pending', index=True)
    status_updated_at = Column(DateTime(timezone=True), nullable=True)
    status_updated_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Processing metadata
    processing_time_ms = Column(Numeric(10, 2), nullable=True)
    model_version = Column(String(50), nullable=True)
    
    # Relationships
    job = relationship("JobDescription", back_populates="match_results")
    resume = relationship("Resume", back_populates="match_results")
    creator = relationship("User", foreign_keys=[created_by], backref="created_matches")
    status_updater = relationship("User", foreign_keys=[status_updated_by], backref="status_updates")
    
    def __repr__(self):
        return f"<MatchResult(id={self.id}, job_id={self.job_id}, resume_id={self.resume_id}, score={self.match_score})>"


# Create indexes for performance
Index('idx_match_job_id', MatchResult.job_id)
Index('idx_match_resume_id', MatchResult.resume_id)
Index('idx_match_score', MatchResult.match_score.desc())
Index('idx_match_created_at', MatchResult.created_at)
Index('idx_match_job_score', MatchResult.job_id, MatchResult.match_score.desc())
Index('idx_match_unique', MatchResult.job_id, MatchResult.resume_id, unique=True)  # Prevent duplicate matches
Index('idx_match_status', MatchResult.status)
Index('idx_match_job_status', MatchResult.job_id, MatchResult.status)