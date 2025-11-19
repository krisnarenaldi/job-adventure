from typing import Any, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_active_user, require_recruiter_or_hiring_manager
from app.repositories.job import JobRepository
from app.repositories.shared_link import SharedLinkRepository
from app.repositories.match_result import MatchResultRepository
from app.repositories.resume import ResumeRepository
from app.repositories.user import UserRepository
from app.schemas.shared_link import (
    SharedLinkCreate,
    SharedLinkResponse,
    SharedLinkListResponse,
    SharedViewResponse
)
from app.models.user import User
from app.services.email_service import EmailService
import uuid
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=SharedLinkResponse)
async def create_shared_link(
    link_data: SharedLinkCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Create a shareable link for job candidates
    """
    try:
        # Initialize repositories
        job_repo = JobRepository(db)
        shared_link_repo = SharedLinkRepository(db)
        
        # Verify job exists and user has access
        job = await job_repo.get(link_data.job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to share candidates for this job"
            )
        
        # Calculate expiration date
        expires_at = None
        if link_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=link_data.expires_in_days)
        
        # Create shared link
        shared_link = await shared_link_repo.create_shared_link(
            job_id=link_data.job_id,
            created_by=current_user.id,
            recipient_email=link_data.recipient_email,
            custom_message=link_data.custom_message,
            expires_at=expires_at
        )
        
        # Construct share URL
        base_url = str(request.base_url).rstrip('/')
        share_url = f"{base_url}/shared/{shared_link.share_token}"
        
        # Send email if recipient email is provided
        if link_data.recipient_email:
            try:
                email_service = EmailService()
                await email_service.send_shared_link_email(
                    recipient_email=link_data.recipient_email,
                    sender_name=current_user.full_name or current_user.email,
                    job_title=job.title,
                    share_url=share_url,
                    custom_message=link_data.custom_message
                )
            except Exception as e:
                logger.warning(f"Failed to send share email: {str(e)}")
                # Don't fail the request if email fails
        
        response = SharedLinkResponse(
            id=shared_link.id,
            job_id=shared_link.job_id,
            share_token=shared_link.share_token,
            recipient_email=shared_link.recipient_email,
            custom_message=shared_link.custom_message,
            expires_at=shared_link.expires_at,
            is_active=shared_link.is_active,
            view_count=shared_link.view_count,
            last_viewed_at=shared_link.last_viewed_at,
            created_at=shared_link.created_at,
            share_url=share_url
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create shared link")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create shared link: {str(e)}"
        )


@router.get("/job/{job_id}", response_model=SharedLinkListResponse)
async def get_shared_links_for_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Get all shared links for a job
    """
    try:
        # Initialize repositories
        job_repo = JobRepository(db)
        shared_link_repo = SharedLinkRepository(db)
        
        # Verify job exists and user has access
        job = await job_repo.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if job.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view shared links for this job"
            )
        
        # Get shared links
        links = await shared_link_repo.get_by_job(job_id)
        
        # Convert to response format
        link_responses = [
            SharedLinkResponse(
                id=link.id,
                job_id=link.job_id,
                share_token=link.share_token,
                recipient_email=link.recipient_email,
                custom_message=link.custom_message,
                expires_at=link.expires_at,
                is_active=link.is_active,
                view_count=link.view_count,
                last_viewed_at=link.last_viewed_at,
                created_at=link.created_at
            )
            for link in links
        ]
        
        return SharedLinkListResponse(
            links=link_responses,
            total=len(link_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get shared links")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shared links: {str(e)}"
        )


@router.delete("/{link_id}")
async def deactivate_shared_link(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Deactivate a shared link
    """
    try:
        shared_link_repo = SharedLinkRepository(db)
        
        # Get the link
        link = await shared_link_repo.get(link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared link not found"
            )
        
        # Check authorization
        if link.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to deactivate this shared link"
            )
        
        # Deactivate the link
        await shared_link_repo.deactivate_link(link_id)
        
        return {"message": "Shared link deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to deactivate shared link")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate shared link: {str(e)}"
        )


@router.get("/view/{token}", response_model=SharedViewResponse)
async def view_shared_candidates(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    View shared candidates (public endpoint, no authentication required)
    """
    try:
        # Initialize repositories
        shared_link_repo = SharedLinkRepository(db)
        job_repo = JobRepository(db)
        match_result_repo = MatchResultRepository(db)
        resume_repo = ResumeRepository(db)
        user_repo = UserRepository(db)
        
        # Get shared link by token
        link = await shared_link_repo.get_by_token(token)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared link not found"
            )
        
        # Check if link is valid
        if not link.is_valid():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This shared link has expired or been deactivated"
            )
        
        # Increment view count
        await shared_link_repo.increment_view_count(link.id)
        
        # Get job details
        job = await job_repo.get(link.job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get creator info
        creator = await user_repo.get(link.created_by)
        shared_by = creator.full_name if creator and creator.full_name else "Recruiter"
        
        # Get match results
        matches = await match_result_repo.get_by_job(link.job_id, skip=0, limit=100)
        
        # Prepare simplified candidate data (no sensitive info)
        candidates = []
        for match in matches:
            resume = await resume_repo.get(match.resume_id)
            
            candidate_data = {
                "rank": len(candidates) + 1,
                "candidate_name": resume.candidate_name if resume else "Unknown",
                "match_score": round(match.match_score, 2),
                "key_strengths": match.key_strengths[:5] if match.key_strengths else [],
                "missing_skills": match.missing_skills[:5] if match.missing_skills else [],
                # Don't include email, phone, or full resume content for privacy
            }
            candidates.append(candidate_data)
        
        # Sort by match score
        candidates.sort(key=lambda x: x["match_score"], reverse=True)
        
        return SharedViewResponse(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description,
            candidates=candidates,
            shared_by=shared_by,
            custom_message=link.custom_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to view shared candidates")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to view shared candidates: {str(e)}"
        )
