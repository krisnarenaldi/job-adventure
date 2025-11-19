from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class ContactBase(BaseModel):
    email: EmailStr
    description: Optional[str] = Field(None, max_length=5000)
    image_data: Optional[str] = None  # Filename of uploaded image file


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

