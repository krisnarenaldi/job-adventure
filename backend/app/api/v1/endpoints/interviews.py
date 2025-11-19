from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.interview import InterviewStatus
from app.schemas.interview import InterviewCreate, InterviewUpdate, InterviewResponse
from app.repositories.interview import InterviewRepository
from app.repositories.match_result import MatchResultRepository
from app.repositories.job import JobRepository
from app.services.email_service import email_service

router = APIRouter()


@router.post("/", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new interview"""
    repo = InterviewRepository(db)
    interview = await repo.create(interview_data, current_user.id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create interview"
        )

    return interview


@router.get("/job/{job_id}", response_model=List[InterviewResponse])
async def get_interviews_by_job(
    job_id: UUID,
    status: Optional[InterviewStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all interviews for a specific job"""
    repo = InterviewRepository(db)
    interviews = await repo.get_by_job_id(job_id, status)
    return interviews


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific interview by ID"""
    repo = InterviewRepository(db)
    interview = await repo.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    return interview


@router.patch("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: UUID,
    interview_data: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an interview"""
    repo = InterviewRepository(db)
    interview = await repo.update(interview_id, interview_data)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_interview(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an interview"""
    repo = InterviewRepository(db)
    interview = await repo.cancel(interview_id, current_user.id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    return None


@router.post("/{interview_id}/send-invitation", response_model=InterviewResponse)
async def send_interview_invitation(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send interview invitation email to candidate"""
    interview_repo = InterviewRepository(db)
    match_repo = MatchResultRepository(db)
    job_repo = JobRepository(db)

    # Get interview
    interview = await interview_repo.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    # Get match result to get candidate info
    match_result = await match_repo.get(interview.match_result_id)
    if not match_result or not match_result.resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate information not found"
        )

    # Get job details
    job = await job_repo.get(interview.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Send email
    try:
        email_service.send_interview_invitation(
            candidate_email=match_result.resume.email or "candidate@example.com",
            candidate_name=match_result.resume.candidate_name or "Candidate",
            job_title=job.title,
            company_name=job.company,
            interview_time=interview.scheduled_time,
            interview_type=interview.interview_type.value,
            meeting_link=interview.meeting_link,
            location=interview.location,
            notes=interview.notes
        )

        # Mark invitation as sent
        interview = await interview_repo.mark_invitation_sent(interview_id)

        return interview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invitation: {str(e)}"
        )


@router.get("/{interview_id}/preview-invitation")
async def preview_interview_invitation(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview interview invitation email"""
    interview_repo = InterviewRepository(db)
    match_repo = MatchResultRepository(db)
    job_repo = JobRepository(db)

    # Get interview
    interview = await interview_repo.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    # Get match result to get candidate info
    match_result = await match_repo.get(interview.match_result_id)
    if not match_result or not match_result.resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate information not found"
        )

    # Get job details
    job = await job_repo.get(interview.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Get preview
    preview = email_service.get_interview_invitation_preview(
        candidate_name=match_result.resume.candidate_name or "Candidate",
        job_title=job.title,
        company_name=job.company,
        interview_time=interview.scheduled_time,
        interview_type=interview.interview_type.value,
        meeting_link=interview.meeting_link,
        location=interview.location,
        notes=interview.notes
    )

    return preview
