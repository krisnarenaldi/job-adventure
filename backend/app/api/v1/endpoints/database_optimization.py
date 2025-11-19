"""
Database optimization endpoints for performance management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from app.db.database import get_db
from app.services.database_optimization_service import db_optimization_service
from app.core.deps import get_current_user
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/optimize/indexes", response_model=Dict[str, Any])
async def create_performance_indexes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create additional performance indexes"""
    
    # Only allow admin users to run optimization
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db_optimization_service.create_missing_indexes(db)
        logger.info(f"Index optimization completed by user {current_user.id}")
        return result
    except Exception as e:
        logger.error(f"Index optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Index optimization failed: {str(e)}")


@router.post("/optimize/analyze", response_model=Dict[str, Any])
async def analyze_database_tables(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run ANALYZE on all tables to update statistics"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db_optimization_service.analyze_tables(db)
        logger.info(f"Table analysis completed by user {current_user.id}")
        return result
    except Exception as e:
        logger.error(f"Table analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Table analysis failed: {str(e)}")


@router.post("/optimize/vacuum", response_model=Dict[str, Any])
async def vacuum_analyze_tables(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run VACUUM ANALYZE on all tables"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db_optimization_service.vacuum_analyze_tables(db)
        logger.info(f"Vacuum analyze completed by user {current_user.id}")
        return result
    except Exception as e:
        logger.error(f"Vacuum analyze failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vacuum analyze failed: {str(e)}")


@router.post("/optimize/settings", response_model=Dict[str, Any])
async def optimize_database_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply database optimization settings"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db_optimization_service.optimize_database_settings(db)
        logger.info(f"Database settings optimization completed by user {current_user.id}")
        return result
    except Exception as e:
        logger.error(f"Database settings optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Settings optimization failed: {str(e)}")


@router.get("/stats/performance", response_model=Dict[str, Any])
async def get_performance_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get database performance statistics"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db_optimization_service.get_query_performance_stats(db)
        return result
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")


@router.get("/stats/size", response_model=Dict[str, Any])
async def get_database_size_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get database size information"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db_optimization_service.get_database_size_info(db)
        return result
    except Exception as e:
        logger.error(f"Failed to get database size info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get size info: {str(e)}")


@router.post("/optimize/full", response_model=Dict[str, Any])
async def run_full_optimization(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run complete database optimization (indexes, analyze, vacuum)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        results = {}
        
        # Create indexes
        results["indexes"] = await db_optimization_service.create_missing_indexes(db)
        
        # Analyze tables
        results["analyze"] = await db_optimization_service.analyze_tables(db)
        
        # Vacuum tables
        results["vacuum"] = await db_optimization_service.vacuum_analyze_tables(db)
        
        # Apply settings
        results["settings"] = await db_optimization_service.optimize_database_settings(db)
        
        logger.info(f"Full database optimization completed by user {current_user.id}")
        
        return {
            "message": "Full database optimization completed",
            "results": results,
            "total_operations": sum([
                results["indexes"]["total_created"],
                results["analyze"]["total_analyzed"],
                results["vacuum"]["total_processed"],
                results["settings"]["total_applied"]
            ])
        }
        
    except Exception as e:
        logger.error(f"Full optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Full optimization failed: {str(e)}")