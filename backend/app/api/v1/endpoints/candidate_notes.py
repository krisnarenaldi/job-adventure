from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.candidate_note import CandidateNoteCreate, CandidateNoteUpdate, CandidateNoteResponse
from app.repositories.candidate_note import CandidateNoteRepository
from app.repositories.match_result import MatchResultRepository

router = APIRouter()


@router.post("/", response_model=CandidateNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: CandidateNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new candidate note"""
    # Verify match result exists
    match_repo = MatchResultRepository(db)
    match_result = await match_repo.get(note_data.match_result_id)
    if not match_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found"
        )
    
    repo = CandidateNoteRepository(db)
    note = await repo.create(note_data, current_user.id)
    
    # Add author information to response
    response = CandidateNoteResponse.model_validate(note)
    response.author_name = current_user.full_name
    response.author_email = current_user.email
    
    return response


@router.get("/match/{match_result_id}", response_model=List[CandidateNoteResponse])
async def get_notes_by_match_result(
    match_result_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notes for a specific match result"""
    # Verify match result exists
    match_repo = MatchResultRepository(db)
    match_result = await match_repo.get(match_result_id)
    if not match_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found"
        )
    
    repo = CandidateNoteRepository(db)
    notes = await repo.get_by_match_result_id(match_result_id, current_user.id)
    
    # Add author information to each note
    response_notes = []
    for note in notes:
        note_response = CandidateNoteResponse.model_validate(note)
        note_response.author_name = note.author.full_name if note.author else None
        note_response.author_email = note.author.email if note.author else None
        response_notes.append(note_response)
    
    return response_notes


@router.get("/{note_id}", response_model=CandidateNoteResponse)
async def get_note(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific note by ID"""
    repo = CandidateNoteRepository(db)
    note = await repo.get_by_id(note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Check if user has permission to view private notes
    if note.is_private and note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this note"
        )
    
    # Add author information
    response = CandidateNoteResponse.model_validate(note)
    response.author_name = note.author.full_name if note.author else None
    response.author_email = note.author.email if note.author else None
    
    return response


@router.patch("/{note_id}", response_model=CandidateNoteResponse)
async def update_note(
    note_id: UUID,
    note_data: CandidateNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a note (only by the author)"""
    repo = CandidateNoteRepository(db)
    note = await repo.update(note_id, note_data, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to update it"
        )
    
    # Add author information
    response = CandidateNoteResponse.model_validate(note)
    response.author_name = current_user.full_name
    response.author_email = current_user.email
    
    return response


@router.delete("/{note_id}", status_code=status.HTTP_200_OK)
async def delete_note(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a note (only by the author)"""
    repo = CandidateNoteRepository(db)
    success = await repo.delete(note_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to delete it"
        )
    return {"status": "success", "message": "Note deleted successfully"}
