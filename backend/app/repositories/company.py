from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """
        Normalize company name for consistent matching:
        - Convert to lowercase
        - Strip whitespace
        - Remove extra spaces between words
        """
        return ' '.join(name.lower().strip().split())

    async def create(self, name: str) -> Company:
        """Create a new company with normalized name"""
        normalized_name = self.normalize_company_name(name)
        company = Company(name=normalized_name)
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID"""
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Company]:
        """
        Get company by name (case-insensitive, normalized)
        Handles variations like "Tech Corp", "tech corp", "TECH CORP"
        """
        normalized_name = self.normalize_company_name(name)
        result = await self.db.execute(
            select(Company).where(func.lower(Company.name) == normalized_name)
        )
        return result.scalar_one_or_none()
