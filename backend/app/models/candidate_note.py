from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid


class CandidateNote(Base):
    __tablename__ = "candidate_notes"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    match_result_id = Column(PostgresUUID(as_uuid=True), ForeignKey("match_results.id"), nullable=False, index=True)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Note content
    note_text = Column(Text, nullable=False)
    is_private = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    match_result = relationship("MatchResult", backref="notes")
    author = relationship("User", backref="candidate_notes")
    
    def __repr__(self):
        return f"<CandidateNote(id={self.id}, match_result_id={self.match_result_id}, author={self.user_id})>"


# Create indexes for performance
Index('idx_note_match_result', CandidateNote.match_result_id)
Index('idx_note_user', CandidateNote.user_id)
Index('idx_note_created_at', CandidateNote.created_at.desc())
Index('idx_note_match_created', CandidateNote.match_result_id, CandidateNote.created_at.desc())
