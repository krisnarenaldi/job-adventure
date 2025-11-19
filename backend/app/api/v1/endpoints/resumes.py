from typing import Any, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_active_user, require_recruiter_or_hiring_manager
from app.repositories.resume import ResumeRepository
from app.services.document_processor import DocumentProcessor
from app.services.resume_parser import ResumeParser
from app.services.embedding_service import EmbeddingService
from app.services.skill_extraction_service import SkillExtractionService
from app.schemas.file_upload import FileType
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeResponse,
    ResumeListResponse,
    ResumeSearchRequest,
    ResumeSimilarityResult,
    ResumeStats,
    ResumeUploadRequest
)
from app.models.user import User
import uuid
import tempfile
import os

router = APIRouter()


@router.post("/", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    resume_data: ResumeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new resume entry
    """
    resume_repo = ResumeRepository(db)
    
    try:
        # Create resume with current user as uploader
        resume_dict = resume_data.model_dump() if hasattr(resume_data, 'model_dump') else resume_data.dict()
        resume_dict["uploaded_by"] = current_user.id
        
        print(f"Creating resume with data: {resume_dict.keys()}")
        resume = await resume_repo.create(resume_dict)
        print(f"Resume created with ID: {resume.id}")
        
        # Process resume asynchronously
        print(f"About to process resume content for {resume.id}")
        await process_resume_content(resume.id, db)
        print(f"Resume processing completed for {resume.id}")
        
        return ResumeResponse.from_orm(resume)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resume: {str(e)}"
        )


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    job_id: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload resume file (PDF or DOCX) and optionally match to a job
    """
    # Validate file type
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Validate file size (10MB limit)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 10MB"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Determine file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension == 'pdf':
            file_type = FileType.PDF
        elif file_extension == 'docx':
            file_type = FileType.DOCX
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and DOCX files are supported"
            )
        
        # Extract text from file
        doc_processor = DocumentProcessor()
        extracted_text = await doc_processor.extract_text(Path(tmp_file_path), file_type)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Get file extension and map to FileType enum
        file_extension = file.filename.split('.')[-1].lower()
        file_type = None
        if file_extension == 'pdf':
            file_type = 'pdf'
        elif file_extension == 'docx':
            file_type = 'docx'
        else:
            file_type = 'txt'  # Default to txt for any other type
            
        # Create resume
        resume_data = ResumeCreate(
            candidate_name=candidate_name,
            email=email,
            phone=phone,
            content=extracted_text,
            original_filename=file.filename,
            file_type=file_type
        )
        print("resume data =",resume_data)

        resume_response = await create_resume(resume_data, db, current_user)

        # If job_id is provided, automatically trigger matching
        if job_id:
            try:
                import uuid as uuid_lib
                from app.repositories.job import JobRepository
                from app.repositories.match_result import MatchResultRepository
                from app.services.matching_engine import get_matching_engine, MatchingRequest

                print(f"Auto-matching resume {resume_response.id} to job {job_id}")

                # Initialize repositories
                job_repo = JobRepository(db)
                resume_repo = ResumeRepository(db)
                match_result_repo = MatchResultRepository(db)

                # Check if this email already has a match for this job
                existing_matches = await match_result_repo.get_by_job(uuid_lib.UUID(job_id))
                for match in existing_matches:
                    existing_resume = await resume_repo.get(match.resume_id)
                    if existing_resume and existing_resume.email == email:
                        print(f"Resume with email {email} already matched to job {job_id}, skipping duplicate matching")
                        return resume_response

                # Verify job exists
                job = await job_repo.get(uuid_lib.UUID(job_id))
                if job:
                    # Get matching engine
                    matching_engine = await get_matching_engine()

                    # Create matching request for this specific resume
                    engine_request = MatchingRequest(
                        job_id=job_id,
                        resume_ids=[str(resume_response.id)],
                        include_explanations=True,
                        min_score_threshold=0.0,
                        max_results=None
                    )

                    # Execute matching
                    matches = await matching_engine.match_resumes_to_job(
                        job_repo, resume_repo, match_result_repo, engine_request
                    )

                    print(f"Auto-matching completed: {len(matches)} matches created")
                else:
                    print(f"Job {job_id} not found, skipping auto-matching")
            except Exception as e:
                # Log error but don't fail the upload
                print(f"Auto-matching failed: {str(e)}")
                import traceback
                traceback.print_exc()

        return resume_response
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resume file: {str(e)}"
        )


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    processed_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get list of resumes
    """
    resume_repo = ResumeRepository(db)
    
    # Get resumes (recruiter/hiring manager access)
    if processed_only:
        resumes = await resume_repo.get_processed_resumes(skip, limit)
    else:
        resumes = await resume_repo.get_all(skip, limit)
    
    # Get total count (simplified)
    total = len(resumes) + skip
    
    return ResumeListResponse(
        resumes=[ResumeResponse.from_orm(resume) for resume in resumes],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/search", response_model=ResumeListResponse)
async def search_resumes(
    candidate_name: str = Query(None),
    email: str = Query(None),
    skills: List[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Search resumes (recruiter/hiring manager only)
    """
    resume_repo = ResumeRepository(db)
    resumes = []
    
    if candidate_name:
        resumes = await resume_repo.get_by_candidate_name(candidate_name, skip, limit)
    elif email:
        resume = await resume_repo.get_by_email(email)
        resumes = [resume] if resume else []
    elif skills:
        resumes = await resume_repo.get_by_skills(skills, skip, limit)
    else:
        resumes = await resume_repo.get_processed_resumes(skip, limit)
    
    total = len(resumes) + skip
    
    return ResumeListResponse(
        resumes=[ResumeResponse.from_orm(resume) for resume in resumes],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats", response_model=ResumeStats)
async def get_resume_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recruiter_or_hiring_manager)
) -> Any:
    """
    Get resume processing statistics
    """
    resume_repo = ResumeRepository(db)
    stats = await resume_repo.get_resume_stats()
    return ResumeStats(**stats)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get resume by ID
    """
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get(resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Recruiters and hiring managers can view all resumes
    
    return ResumeResponse.from_orm(resume)


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: uuid.UUID,
    resume_update: ResumeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update resume
    """
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get(resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Recruiters and hiring managers can update resumes
    
    # Update resume
    update_data = resume_update.dict(exclude_unset=True)
    updated_resume = await resume_repo.update(resume_id, update_data)
    
    if not updated_resume:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resume"
        )
    
    return ResumeResponse.from_orm(updated_resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete resume
    """
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get(resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Recruiters and hiring managers can delete resumes
    
    # Delete resume
    success = await resume_repo.delete(resume_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )
    
    return {"message": "Resume deleted successfully"}


async def process_resume_content(resume_id: uuid.UUID, db: AsyncSession):
    """
    Process resume content to extract skills and generate embeddings
    """
    try:
        print(f"Starting resume processing for {resume_id}")
        resume_repo = ResumeRepository(db)
        resume = await resume_repo.get(resume_id)
        
        if not resume:
            print(f"Resume {resume_id} not found")
            return
        
        print(f"Resume found, content length: {len(resume.content) if resume.content else 0}")
        
        # Extract sections and skills
        resume_parser = ResumeParser()
        print("Resume parser created")
        sections = await resume_parser.extract_sections(resume.content)
        print(f"Sections extracted: {list(sections.keys()) if sections else 'None'}")
        
        # Use skill extractor
        skill_extractor = SkillExtractionService()
        print("Skill extractor created")
        extracted_skills_obj = await skill_extractor.extract_skills(resume.content)
        print(f"Skills extracted: {extracted_skills_obj}")
        # Convert to simple list of strings for database
        extracted_skills = extracted_skills_obj.all_skills if hasattr(extracted_skills_obj, 'all_skills') else []
        print(f"Skills list for DB: {extracted_skills}")
        
        # Use embedding service
        embedding_service = EmbeddingService()
        print("Embedding service created")
        await embedding_service.initialize()
        print("Embedding service initialized")
        embedding = await embedding_service.generate_embedding(resume.content)
        print(f"Embedding generated, length: {len(embedding) if embedding else 0}")
        
        # Update resume with processed data
        processed_data = {
            "sections": sections,
            "extracted_skills": extracted_skills,
            "embedding": embedding
        }
        
        print(f"Marking resume as processed with data: {list(processed_data.keys())}")
        result = await resume_repo.mark_as_processed(resume_id, processed_data)
        print(f"Resume marked as processed: {result}")
        
    except Exception as e:
        print(f"Failed to process resume {resume_id}: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise exception to avoid breaking the API call