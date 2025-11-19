from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Path as FastAPIPath
from pydantic import BaseModel

from app.services.document_processor import document_processor
from app.core.exceptions import DocumentExtractionError
from app.services.file_service import file_service
from app.schemas.file_upload import FileType


router = APIRouter()


class DocumentTextResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    raw_text: str
    normalized_text: str
    text_length: int
    is_valid: bool
    metadata: Dict[str, Any]


class TextExtractionRequest(BaseModel):
    file_id: str
    normalize: bool = True


@router.post("/extract-text", response_model=DocumentTextResponse)
async def extract_document_text(request: TextExtractionRequest):
    """
    Extract text from an uploaded document.
    
    Args:
        request: Contains file_id and processing options
        
    Returns:
        Extracted and optionally normalized text with metadata
    """
    try:
        # Find the uploaded file
        upload_dir = file_service.upload_dir
        matching_files = list(upload_dir.glob(f"{request.file_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        
        # Determine file type from extension
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
        raw_text = await document_processor.extract_text(file_path, file_type)
        
        # Normalize text if requested
        normalized_text = raw_text
        if request.normalize:
            normalized_text = await document_processor.normalize_text(raw_text)
        
        # Validate extracted text
        is_valid = document_processor.validate_extracted_text(normalized_text)
        
        # Get document metadata
        metadata = await document_processor.get_document_metadata(file_path, file_type)
        
        return DocumentTextResponse(
            file_id=request.file_id,
            filename=file_path.name,
            file_type=file_type.value,
            raw_text=raw_text,
            normalized_text=normalized_text,
            text_length=len(normalized_text),
            is_valid=is_valid,
            metadata=metadata
        )
    
    except DocumentExtractionError as e:
        raise HTTPException(status_code=422, detail=f"Document processing failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


@router.get("/extract-text/{file_id}", response_model=DocumentTextResponse)
async def extract_document_text_by_id(
    file_id: str = FastAPIPath(..., description="File ID to extract text from"),
    normalize: bool = True
):
    """
    Extract text from an uploaded document by file ID.
    
    Args:
        file_id: ID of the uploaded file
        normalize: Whether to normalize the extracted text
        
    Returns:
        Extracted and optionally normalized text with metadata
    """
    request = TextExtractionRequest(file_id=file_id, normalize=normalize)
    return await extract_document_text(request)


@router.get("/validate-text/{file_id}")
async def validate_document_text(file_id: str = FastAPIPath(..., description="File ID to validate")):
    """
    Validate that text can be extracted from a document without returning the full text.
    Useful for checking document integrity before processing.
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
        
        # Extract a small sample of text to validate
        raw_text = await document_processor.extract_text(file_path, file_type)
        
        # Validate without returning full text
        is_valid = document_processor.validate_extracted_text(raw_text)
        text_preview = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
        
        return {
            "file_id": file_id,
            "filename": file_path.name,
            "file_type": file_type.value,
            "is_valid": is_valid,
            "text_length": len(raw_text),
            "text_preview": text_preview,
            "can_extract": True
        }
    
    except DocumentExtractionError as e:
        return {
            "file_id": file_id,
            "is_valid": False,
            "can_extract": False,
            "error": str(e)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")