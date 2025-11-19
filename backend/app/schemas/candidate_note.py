from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class CandidateNoteBase(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=10000)
    is_private: bool = False


class CandidateNoteCreate(CandidateNoteBase):
    match_result_id: UUID


class CandidateNoteUpdate(BaseModel):
    note_text: Optional[str] = Field(None, min_length=1, max_length=10000)
    is_private: Optional[bool] = None


class CandidateNoteResponse(CandidateNoteBase):
    id: UUID
    match_result_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Optional author information
    author_name: Optional[str] = None
    author_email: Optional[str] = None

    class Config:
        from_attributes = True
