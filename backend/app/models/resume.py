from sqlalchemy import Column, String, Text, DateTime, Index, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.database import Base
import uuid


class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    candidate_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    
    # Document content
    content = Column(Text, nullable=False)  # Full extracted text
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)  # Path to stored file
    file_type = Column(String(10), nullable=True)  # pdf, docx
    
    # Structured sections
    sections = Column(JSON, nullable=True)  # {"experience": "...", "skills": "...", "education": "..."}
    extracted_skills = Column(ARRAY(String), nullable=True)
    experience_years = Column(String(20), nullable=True)
    education_level = Column(String(100), nullable=True)
    
    # AI-related fields
    embedding = Column(Vector(384), nullable=True)  # Sentence transformer embedding dimension
    
    # Metadata
    uploaded_by = Column(PostgresUUID(as_uuid=True), nullable=True)  # User who uploaded the resume
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    is_processed = Column(String(10), default="false")
    
    # Relationships
    match_results = relationship("MatchResult", back_populates="resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, candidate_name={self.candidate_name}, email={self.email})>"


# Create indexes for performance
Index('idx_resume_candidate_name', Resume.candidate_name)
Index('idx_resume_email', Resume.email)
Index('idx_resume_uploaded_at', Resume.uploaded_at)
Index('idx_resume_processed', Resume.is_processed)
Index('idx_resume_embedding', Resume.embedding, postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'})