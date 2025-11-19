from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from app.core.security import get_password_hash, verify_password
import uuid


class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by id"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        result = await self.db.execute(
            select(User)
            .where(User.role == role)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_company(self, company_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by company ID"""
        result = await self.db.execute(
            select(User)
            .where(User.company_id == company_id)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        """Deactivate a user (soft delete)"""
        return await self.update(user_id, {"is_active": False}) is not None
    
    async def activate_user(self, user_id: uuid.UUID) -> bool:
        """Activate a user"""
        return await self.update(user_id, {"is_active": True}) is not None
    
    async def create_user(self, email: str, password: str, full_name: Optional[str] = None, 
                         role: UserRole = UserRole.RECRUITER, company_id: Optional[uuid.UUID] = None) -> User:
        """Create a new user with hashed password"""
        hashed_password = get_password_hash(password)
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "role": role,
            "company_id": company_id,
            "is_active": True
        }
        return await self.create(user_data)
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def update_password(self, user_id: uuid.UUID, hashed_password: str) -> bool:
        """Update a user's password"""
        updated_user = await self.update(user_id, {"hashed_password": hashed_password})
        return updated_user is not None