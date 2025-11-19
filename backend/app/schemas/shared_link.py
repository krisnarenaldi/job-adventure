from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class SharedLinkCreate(BaseModel):
    """Schema for creating a shared link"""
    job_id: uuid.UUID
    recipient_email: Optional[str] = None
    custom_message: Optional[str] = None
    expires_in_days: Optional[int] = None  # Number of days until expiration
    
    @field_validator('expires_in_days')
    def validate_expires_in_days(cls, v):
        if v is not None and (v < 1 or v > 365):
            raise ValueError('Expiration must be between 1 and 365 days')
        return v
    
    @field_validator('custom_message')
    def validate_custom_message(cls, v):
        if v and len(v) > 1000:
            raise ValueError('Custom message must be 1000 characters or less')
        return v
    
    model_config = ConfigDict(from_attributes=True)


class SharedLinkResponse(BaseModel):
    """Schema for shared link response"""
    id: uuid.UUID
    job_id: uuid.UUID
    share_token: str
    recipient_email: Optional[str] = None
    custom_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    view_count: int
    last_viewed_at: Optional[datetime] = None
    created_at: datetime
    share_url: Optional[str] = None  # Full URL to be constructed in endpoint
    
    model_config = ConfigDict(from_attributes=True)


class SharedLinkListResponse(BaseModel):
    """Schema for list of shared links"""
    links: list[SharedLinkResponse]
    total: int
    
    model_config = ConfigDict(from_attributes=True)


class SharedViewResponse(BaseModel):
    """Schema for shared view data (what external users see)"""
    job_title: str
    job_company: str
    job_description: str
    candidates: list[dict]  # Simplified candidate data
    shared_by: str  # Name or email of person who shared
    custom_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
