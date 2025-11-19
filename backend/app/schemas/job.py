from __future__ import annotations
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class JobBase(BaseModel):
    title: str
    company: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    skills_required: Optional[List[str]] = None


class JobCreate(JobBase):
    @field_validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Title must be at least 3 characters long')
        return v.strip()
    
    @field_validator('company')
    def validate_company(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()
    
    @field_validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        return v.strip()
    
    @field_validator('requirements')
    def validate_requirements(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Requirements must be at least 10 characters long')
        return v.strip()


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    skills_required: Optional[List[str]] = None
    is_active: Optional[bool] = None


class JobInDB(JobBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class JobResponse(JobInDB):
    candidate_count: Optional[int] = 0


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    skip: int
    limit: int


class JobSearchRequest(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None


class JobSimilarityResult(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    description: str
    similarity: float


class JobStatusUpdate(BaseModel):
    is_active: bool