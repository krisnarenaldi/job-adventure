from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.schemas.file_upload import FileUploadResponse, FileValidationError
from app.services.file_service import file_service


router = APIRouter()


@router.post("/upload/job-description", response_model=FileUploadResponse)
async def upload_job_description(
    file: UploadFile = File(..., description="Job description file (PDF or TXT)")
):
    """
    Upload a job description file.
    Accepts PDF and TXT formats.
    """
    try:
        # Validate file type for job descriptions (PDF and TXT only)
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_extension = file.filename.lower().split('.')[-1]
        if file_extension not in ['pdf', 'txt']:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type for job description. Allowed types: PDF, TXT"
            )
        
        # Save file
        file_info = await file_service.save_file(file)
        
        return FileUploadResponse(
            file_id=file_info.filename.split('.')[0],  # Extract UUID part
            filename=file.filename,
            file_type=file_info.file_type,
            file_size=file_info.file_size,
            upload_path=str(file_service.get_file_path(file_info.filename)),
            message="Job description uploaded successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/resume", response_model=FileUploadResponse)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)")
):
    """
    Upload a resume file.
    Accepts PDF and DOCX formats.
    """
    try:
        # Validate file type for resumes (PDF and DOCX only)
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_extension = file.filename.lower().split('.')[-1]
        if file_extension not in ['pdf', 'docx']:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type for resume. Allowed types: PDF, DOCX"
            )
        
        # Save file
        file_info = await file_service.save_file(file)
        
        return FileUploadResponse(
            file_id=file_info.filename.split('.')[0],  # Extract UUID part
            filename=file.filename,
            file_type=file_info.file_type,
            file_size=file_info.file_size,
            upload_path=str(file_service.get_file_path(file_info.filename)),
            message="Resume uploaded successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/resumes/batch", response_model=List[FileUploadResponse])
async def upload_multiple_resumes(
    files: List[UploadFile] = File(..., description="Multiple resume files (PDF or DOCX)")
):
    """
    Upload multiple resume files at once.
    Accepts PDF and DOCX formats.
    """
    if len(files) > 50:  # Reasonable limit for batch upload
        raise HTTPException(status_code=400, detail="Too many files. Maximum 50 files allowed per batch")
    
    results = []
    errors = []
    
    for file in files:
        try:
            # Validate file type for resumes
            if not file.filename:
                errors.append(f"File without name skipped")
                continue
            
            file_extension = file.filename.lower().split('.')[-1]
            if file_extension not in ['pdf', 'docx']:
                errors.append(f"File {file.filename}: Invalid file type. Allowed types: PDF, DOCX")
                continue
            
            # Save file
            file_info = await file_service.save_file(file)
            
            results.append(FileUploadResponse(
                file_id=file_info.filename.split('.')[0],
                filename=file.filename,
                file_type=file_info.file_type,
                file_size=file_info.file_size,
                upload_path=str(file_service.get_file_path(file_info.filename)),
                message="Resume uploaded successfully"
            ))
        
        except Exception as e:
            errors.append(f"File {file.filename}: {str(e)}")
    
    # If there were errors but some files succeeded, return partial success
    if errors and results:
        return JSONResponse(
            status_code=207,  # Multi-Status
            content={
                "successful_uploads": len(results),
                "failed_uploads": len(errors),
                "results": [result.dict() for result in results],
                "errors": errors
            }
        )
    
    # If all files failed
    if errors and not results:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "All file uploads failed",
                "errors": errors
            }
        )
    
    return results


@router.get("/upload/validate/{file_id}")
async def validate_uploaded_file(file_id: str):
    """
    Validate that an uploaded file exists and is accessible.
    """
    # Find file by ID (UUID part of filename)
    upload_dir = file_service.upload_dir
    matching_files = list(upload_dir.glob(f"{file_id}.*"))
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    file_stats = file_path.stat()
    return {
        "file_id": file_id,
        "filename": file_path.name,
        "file_size": file_stats.st_size,
        "exists": True,
        "message": "File is valid and accessible"
    }


@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: str):
    """
    Delete an uploaded file.
    """
    # Find file by ID
    upload_dir = file_service.upload_dir
    matching_files = list(upload_dir.glob(f"{file_id}.*"))
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    success = await file_service.delete_file(file_path.name)
    
    if success:
        return {"message": "File deleted successfully", "file_id": file_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file")