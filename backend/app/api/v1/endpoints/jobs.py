from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_active_user, require_recruiter_or_hiring_manager
from app.repositories.job import JobRepository
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobSearchRequest,
    JobSimilarityResult,
    JobStatusUpdate
)
from app.models.user import User
import uuid

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Create a new job description
    """
    job_repo = JobRepository(db)
    
    try:
        # Create job with current user as creator
        job_dict = job_data.dict()
        job_dict["created_by"] = current_user.id
        
        job = await job_repo.create(job_dict)
        
        # Generate embedding for the job description
        try:
            embedding_service = EmbeddingService()
            full_text = f"{job.title} {job.description} {job.requirements}"
            embedding = await embedding_service.generate_embedding(full_text)
            await job_repo.update_embedding(job.id, embedding)
        except Exception as e:
            # Log error but don't fail job creation
            print(f"Failed to generate embedding for job {job.id}: {e}")
        
        return JobResponse.from_orm(job)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def upload_job_description(
    title: str,
    company: str,
    file: UploadFile = File(...),
    location: str = None,
    salary_range: str = None,
    employment_type: str = None,
    experience_level: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Upload job description from file (PDF or text)
    """
    # Validate file type
    if file.content_type not in ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX, and text files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Extract text from file
        doc_processor = DocumentProcessor()
        extracted_text = await doc_processor.extract_text(tmp_file_path, file.content_type)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Split content into description and requirements (simple heuristic)
        text_parts = extracted_text.split('\n\n')
        if len(text_parts) >= 2:
            description = '\n\n'.join(text_parts[:len(text_parts)//2])
            requirements = '\n\n'.join(text_parts[len(text_parts)//2:])
        else:
            description = extracted_text
            requirements = "Requirements to be specified"
        
        # Create job
        job_data = JobCreate(
            title=title,
            company=company,
            description=description,
            requirements=requirements,
            location=location,
            salary_range=salary_range,
            employment_type=employment_type,
            experience_level=experience_level
        )
        
        return await create_job(job_data, db, current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process job description file: {str(e)}"
        )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get list of job descriptions
    """
    job_repo = JobRepository(db)
    
    # Debug info
    print(f"Current user ID: {current_user.id}")
    print(f"Current user role: {current_user.role}")
    print(f"Current user company_id: {current_user.company_id}")
    
    # Get jobs based on user role and company
    if current_user.role.lower() in ["recruiter", "hiring_manager"]:
        # If user has a company, show all jobs from that company (team collaboration)
        # Otherwise, show only jobs created by the user
        if current_user.company_id:
            print(f"Fetching jobs for company {current_user.company_id}")
            jobs = await job_repo.get_by_company_id(current_user.company_id, skip, limit)
            print(f"Found {len(jobs)} jobs for company {current_user.company_id}")
        else:
            print(f"Fetching jobs for user {current_user.id} (no company)")
            jobs = await job_repo.get_by_creator(current_user.id, skip, limit)
            print(f"Found {len(jobs)} jobs for user {current_user.id}")
    else:
        # Show all active jobs
        print(f"Fetching active jobs for non-recruiter user {current_user.id}")
        jobs = await job_repo.get_active_jobs(skip, limit)
        print(f"Found {len(jobs)} active jobs")
    
    # Get candidate count for each job
    from app.repositories.match_result import MatchResultRepository
    from sqlalchemy import select, func, distinct
    from app.models.match_result import MatchResult
    
    job_responses = []
    for job in jobs:
        # Count distinct resume matches for this job
        count_result = await db.execute(
            select(func.count(distinct(MatchResult.resume_id))).where(MatchResult.job_id == job.id)
        )
        candidate_count = count_result.scalar() or 0
        
        # Debug info
        print(f"Job ID: {job.id}, Candidate Count: {candidate_count}")
        
        # Create response with candidate count
        job_response = JobResponse.model_validate(job)
        job_response.candidate_count = candidate_count
        job_responses.append(job_response)
    
    # Get total count (simplified - in production, implement proper counting)
    total = len(jobs) + skip  # Approximation
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/search", response_model=JobListResponse)
async def search_jobs(
    title: str = Query(None),
    company: str = Query(None),
    skills: List[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Search job descriptions
    """
    job_repo = JobRepository(db)
    jobs = []
    
    if title:
        jobs = await job_repo.search_by_title(title, skip, limit)
    elif company:
        jobs = await job_repo.get_by_company(company, skip, limit)
    elif skills:
        jobs = await job_repo.get_by_skills(skills, skip, limit)
    else:
        jobs = await job_repo.get_active_jobs(skip, limit)
    
    total = len(jobs) + skip  # Approximation
    
    return JobListResponse(
        jobs=[JobResponse.from_orm(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get job description by ID
    """
    job_repo = JobRepository(db)
    job = await job_repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Count candidate matches for this job
    from sqlalchemy import select, func, distinct
    from app.models.match_result import MatchResult
    
    count_result = await db.execute(
        select(func.count(distinct(MatchResult.resume_id))).where(MatchResult.job_id == job.id)
    )
    candidate_count = count_result.scalar() or 0
    
    # Create response with candidate count
    job_response = JobResponse.from_orm(job)
    job_response.candidate_count = candidate_count
    
    return job_response


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: uuid.UUID,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Update job description
    """
    job_repo = JobRepository(db)
    job = await job_repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check if user can update this job
    if job.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Update job
    update_data = job_update.dict(exclude_unset=True)
    updated_job = await job_repo.update(job_id, update_data)
    
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )
    
    # Regenerate embedding if content changed
    if any(field in update_data for field in ["title", "description", "requirements"]):
        try:
            embedding_service = EmbeddingService()
            full_text = f"{updated_job.title} {updated_job.description} {updated_job.requirements}"
            embedding = await embedding_service.generate_embedding(full_text)
            await job_repo.update_embedding(job_id, embedding)
        except Exception as e:
            print(f"Failed to update embedding for job {job_id}: {e}")
    
    return JobResponse.from_orm(updated_job)


@router.patch("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: uuid.UUID,
    status_update: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Update job active/inactive status
    """
    job_repo = JobRepository(db)
    job = await job_repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check if user can update this job
    if job.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Update job status
    if status_update.is_active:
        success = await job_repo.activate_job(job_id)
    else:
        success = await job_repo.deactivate_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job status"
        )
    
    # Get updated job
    updated_job = await job_repo.get(job_id)
    return JobResponse.from_orm(updated_job)


@router.delete("/{job_id}")
async def delete_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Delete (deactivate) job description
    """
    job_repo = JobRepository(db)
    job = await job_repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check if user can delete this job
    if job.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    # Soft delete
    success = await job_repo.deactivate_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )
    
    return {"message": "Job deleted successfully"}