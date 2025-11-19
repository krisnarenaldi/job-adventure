from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.database import Base
import uuid


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(100), nullable=True)
    employment_type = Column(String(50), nullable=True)  # full-time, part-time, contract
    experience_level = Column(String(50), nullable=True)  # entry, mid, senior
    skills_required = Column(ARRAY(String), nullable=True)
    
    # AI-related fields
    embedding = Column(Vector(384), nullable=True)  # Sentence transformer embedding dimension
    
    # Metadata
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("User", backref="created_jobs")
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")
    shared_links = relationship("SharedLink", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobDescription(id={self.id}, title={self.title}, company={self.company})>"


# Create indexes for performance
Index('idx_job_created_by', JobDescription.created_by)
Index('idx_job_created_at', JobDescription.created_at)
Index('idx_job_title_company', JobDescription.title, JobDescription.company)
Index('idx_job_embedding', JobDescription.embedding, postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'})