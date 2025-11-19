from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", backref="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"


# Create indexes for performance
Index('idx_company_name', Company.name)
