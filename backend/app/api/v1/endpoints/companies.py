from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.company import Company
from pydantic import BaseModel

router = APIRouter()


class CompanyResponse(BaseModel):
    id: str
    name: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    search: str = Query(None, description="Search company names"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get list of companies for autocomplete
    Public endpoint - no authentication required for registration
    """
    query = select(Company).order_by(Company.name)
    
    # Filter by search term if provided
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(Company.name.ilike(search_term))
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    companies = result.scalars().all()
    
    return [
        CompanyResponse(id=str(company.id), name=company.name)
        for company in companies
    ]
