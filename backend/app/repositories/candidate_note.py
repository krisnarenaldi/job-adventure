from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.candidate_note import CandidateNote
from app.schemas.candidate_note import CandidateNoteCreate, CandidateNoteUpdate


class CandidateNoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, note_data: CandidateNoteCreate, user_id: UUID) -> CandidateNote:
        """Create a new candidate note"""
        note = CandidateNote(
            **note_data.model_dump(),
            user_id=user_id
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_by_id(self, note_id: UUID) -> Optional[CandidateNote]:
        """Get note by ID"""
        result = await self.db.execute(
            select(CandidateNote).options(selectinload(CandidateNote.author)).where(CandidateNote.id == note_id)
        )
        return result.scalar_one_or_none()

    async def get_by_match_result_id(self, match_result_id: UUID, user_id: Optional[UUID] = None) -> List[CandidateNote]:
        """
        Get all notes for a match result
        If user_id is provided, include private notes only for that user
        """
        query = select(CandidateNote).options(selectinload(CandidateNote.author)).where(
            CandidateNote.match_result_id == match_result_id
        )

        if user_id:
            # Show public notes and user's own private notes
            query = query.where(
                (CandidateNote.is_private == False) | (CandidateNote.user_id == user_id)
            )
        else:
            # Only show public notes if no user specified
            query = query.where(CandidateNote.is_private == False)

        query = query.order_by(CandidateNote.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, note_id: UUID, note_data: CandidateNoteUpdate, user_id: UUID) -> Optional[CandidateNote]:
        """Update a note (only by the author)"""
        note = await self.get_by_id(note_id)
        if not note or note.user_id != user_id:
            return None

        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)

        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def delete(self, note_id: UUID, user_id: UUID) -> bool:
        """Delete a note (only by the author)"""
        note = await self.get_by_id(note_id)
        if not note or note.user_id != user_id:
            return False

        # mark for deletion and commit
        self.db.delete(note)
        await self.db.commit()
        return True

    async def get_notes_by_user(self, user_id: UUID, limit: int = 50) -> List[CandidateNote]:
        """Get all notes created by a specific user"""
        result = await self.db.execute(
            select(CandidateNote)
            .where(CandidateNote.user_id == user_id)
            .order_by(CandidateNote.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
