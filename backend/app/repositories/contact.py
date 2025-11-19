from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.contact import Contact
from app.schemas.contact import ContactCreate


class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, contact_data: ContactCreate, user_id: UUID) -> Contact:
        """Create a new contact submission"""
        contact = Contact(
            email=contact_data.email,
            description=contact_data.description,
            image_data=contact_data.image_data,
            user_id=user_id
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_by_id(self, contact_id: UUID) -> Optional[Contact]:
        """Get contact by ID"""
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID, limit: int = 100) -> List[Contact]:
        """Get all contacts submitted by a specific user"""
        result = await self.db.execute(
            select(Contact)
            .where(Contact.user_id == user_id)
            .order_by(Contact.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get all contacts with pagination"""
        result = await self.db.execute(
            select(Contact)
            .order_by(Contact.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

