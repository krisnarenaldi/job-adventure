from __future__ import annotations
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ResumeBase(BaseModel):
    candidate_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeCreate(ResumeBase):
    content: str
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    
    @field_validator('candidate_name')
    def validate_candidate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Candidate name must be at least 2 characters long')
        return v.strip()
    
    @field_validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError('Resume content must be at least 50 characters long')
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class ResumeUpdate(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    sections: Optional[Dict[str, Any]] = None
    extracted_skills: Optional[List[str]] = None
    experience_years: Optional[str] = None
    education_level: Optional[str] = None


class ResumeInDB(ResumeBase):
    id: uuid.UUID
    content: str
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    sections: Optional[Dict[str, Any]] = None
    extracted_skills: Optional[List[str]] = None
    experience_years: Optional[str] = None
    education_level: Optional[str] = None
    uploaded_by: Optional[uuid.UUID] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    is_processed: str
    
    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(ResumeInDB):
    pass


class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total: int
    skip: int
    limit: int


class ResumeSearchRequest(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_level: Optional[str] = None
    processed_only: bool = True


class ResumeSimilarityResult(BaseModel):
    id: uuid.UUID
    candidate_name: str
    email: Optional[str] = None
    content_preview: str
    similarity: float


class ResumeStats(BaseModel):
    total: int
    processed: int
    unprocessed: int


class ResumeUploadRequest(BaseModel):
    candidate_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None