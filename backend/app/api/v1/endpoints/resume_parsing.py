from typing import Dict, List
from fastapi import APIRouter, HTTPException, Path as FastAPIPath
from pydantic import BaseModel

from app.services.resume_parser import resume_parser, ResumeParsingError
from app.services.document_processor import document_processor
from app.services.file_service import file_service
from app.schemas.file_upload import FileType


router = APIRouter()


class ResumeSectionsResponse(BaseModel):
    file_id: str
    filename: str
    sections: Dict[str, str]
    validation_results: Dict[str, bool]
    total_sections: int
    valid_sections: int


class DetailedSkillsResponse(BaseModel):
    file_id: str
    skills_by_category: Dict[str, List[str]]
    total_skills: int


class ResumeParsingRequest(BaseModel):
    file_id: str
    extract_skills: bool = True
    validate_sections: bool = True


@router.post("/parse-resume", response_model=ResumeSectionsResponse)
async def parse_resume_sections(request: ResumeParsingRequest):
    """
    Parse a resume file and extract structured sections.
    
    Args:
        request: Contains file_id and parsing options
        
    Returns:
        Extracted resume sections with validation results
    """
    try:
        # Find the uploaded file
        upload_dir = file_service.upload_dir
        matching_files = list(upload_dir.glob(f"{request.file_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        
        # Determine file type
        file_extension = file_path.suffix.lower()
        if file_extension == '.pdf':
            file_type = FileType.PDF
        elif file_extension == '.docx':
            file_type = FileType.DOCX
        elif file_extension == '.txt':
            file_type = FileType.TXT
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type for resume parsing: {file_extension}")
        
        # Extract text from document
        resume_text = await document_processor.extract_text(file_path, file_type)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=422, detail="Resume text is too short or empty")
        
        # Normalize text
        normalized_text = await document_processor.normalize_text(resume_text)
        
        # Extract sections
        sections = await resume_parser.extract_sections(normalized_text)
        
        # Validate sections if requested
        validation_results = {}
        if request.validate_sections:
            validation_results = resume_parser.validate_extracted_sections(sections)
        
        valid_sections_count = sum(1 for is_valid in validation_results.values() if is_valid)
        
        return ResumeSectionsResponse(
            file_id=request.file_id,
            filename=file_path.name,
            sections=sections,
            validation_results=validation_results,
            total_sections=len(sections),
            valid_sections=valid_sections_count
        )
    
    except ResumeParsingError as e:
        raise HTTPException(status_code=422, detail=f"Resume parsing failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")


@router.get("/parse-resume/{file_id}", response_model=ResumeSectionsResponse)
async def parse_resume_by_id(
    file_id: str = FastAPIPath(..., description="File ID of the resume to parse"),
    extract_skills: bool = True,
    validate_sections: bool = True
):
    """
    Parse a resume file by ID and extract structured sections.
    
    Args:
        file_id: ID of the uploaded resume file
        extract_skills: Whether to extract detailed skills
        validate_sections: Whether to validate extracted sections
        
    Returns:
        Extracted resume sections with validation results
    """
    request = ResumeParsingRequest(
        file_id=file_id,
        extract_skills=extract_skills,
        validate_sections=validate_sections
    )
    return await parse_resume_sections(request)


@router.post("/extract-skills", response_model=DetailedSkillsResponse)
async def extract_detailed_skills(request: ResumeParsingRequest):
    """
    Extract detailed skills categorization from a resume.
    
    Args:
        request: Contains file_id and parsing options
        
    Returns:
        Categorized skills extracted from the resume
    """
    try:
        # Find the uploaded file
        upload_dir = file_service.upload_dir
        matching_files = list(upload_dir.glob(f"{request.file_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        
        # Determine file type
        file_extension = file_path.suffix.lower()
        if file_extension == '.pdf':
            file_type = FileType.PDF
        elif file_extension == '.docx':
            file_type = FileType.DOCX
        elif file_extension == '.txt':
            file_type = FileType.TXT
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # Extract text from document
        resume_text = await document_processor.extract_text(file_path, file_type)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=422, detail="Resume text is too short or empty")
        
        # Extract detailed skills
        skills_by_category = await resume_parser.extract_skills_detailed(resume_text)
        
        # Count total skills
        total_skills = sum(len(skills) for skills in skills_by_category.values())
        
        return DetailedSkillsResponse(
            file_id=request.file_id,
            skills_by_category=skills_by_category,
            total_skills=total_skills
        )
    
    except ResumeParsingError as e:
        raise HTTPException(status_code=422, detail=f"Skills extraction failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skills extraction failed: {str(e)}")


@router.get("/extract-skills/{file_id}", response_model=DetailedSkillsResponse)
async def extract_skills_by_id(file_id: str = FastAPIPath(..., description="File ID of the resume")):
    """
    Extract detailed skills from a resume by file ID.
    
    Args:
        file_id: ID of the uploaded resume file
        
    Returns:
        Categorized skills extracted from the resume
    """
    request = ResumeParsingRequest(file_id=file_id, extract_skills=True)
    return await extract_detailed_skills(request)


@router.get("/validate-resume/{file_id}")
async def validate_resume_structure(file_id: str = FastAPIPath(..., description="File ID of the resume")):
    """
    Validate the structure and content quality of a resume without full parsing.
    
    Args:
        file_id: ID of the uploaded resume file
        
    Returns:
        Validation results and quality metrics
    """
    try:
        # Find the uploaded file
        upload_dir = file_service.upload_dir
        matching_files = list(upload_dir.glob(f"{file_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        
        # Determine file type
        file_extension = file_path.suffix.lower()
        if file_extension == '.pdf':
            file_type = FileType.PDF
        elif file_extension == '.docx':
            file_type = FileType.DOCX
        elif file_extension == '.txt':
            file_type = FileType.TXT
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # Extract text
        resume_text = await document_processor.extract_text(file_path, file_type)
        
        # Basic validation
        is_valid_text = document_processor.validate_extracted_text(resume_text)
        
        # Quick section detection
        sections = await resume_parser.extract_sections(resume_text)
        section_count = len(sections)
        
        # Check for key resume elements
        has_contact = any('contact' in section.lower() for section in sections.keys())
        has_experience = any('experience' in section.lower() for section in sections.keys())
        has_skills = any('skill' in section.lower() for section in sections.keys())
        
        return {
            "file_id": file_id,
            "filename": file_path.name,
            "is_valid_text": is_valid_text,
            "text_length": len(resume_text),
            "sections_found": section_count,
            "has_contact_info": has_contact,
            "has_experience": has_experience,
            "has_skills": has_skills,
            "quality_score": (
                (0.3 if is_valid_text else 0) +
                (0.2 if has_contact else 0) +
                (0.3 if has_experience else 0) +
                (0.2 if has_skills else 0)
            ),
            "recommendations": [
                "Add contact information section" if not has_contact else None,
                "Add work experience section" if not has_experience else None,
                "Add skills section" if not has_skills else None,
                "Document appears to be too short" if len(resume_text) < 200 else None
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume validation failed: {str(e)}")