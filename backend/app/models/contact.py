from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from app.db.database import Base
import uuid


class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_data = Column(Text, nullable=True)  # Base64 encoded image data
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Contact(id={self.id}, email={self.email}, user_id={self.user_id})>"

