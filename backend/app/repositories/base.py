from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from app.db.database import Base
import uuid

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """Get a record by ID"""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering"""
        query = select(self.model)
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update(self, id: uuid.UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record by ID"""
        # First check if record exists
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        # Update the record
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        await self.db.commit()
        
        # Return updated record
        return await self.get(id)
    
    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by ID"""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        query = select(func.count(self.model.id))
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def exists(self, id: uuid.UUID) -> bool:
        """Check if a record exists by ID"""
        result = await self.db.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return result.scalar() > 0