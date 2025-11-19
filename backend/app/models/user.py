from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, UUID, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from app.db.database import Base
import enum
import uuid


class UserRole(str, enum.Enum):
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.RECRUITER)
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    # is_active = Column(String(10), default="true")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"