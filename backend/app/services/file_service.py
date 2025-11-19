import os
import uuid
import aiofiles
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from pathlib import Path

from app.core.config import settings
from app.schemas.file_upload import FileType, UploadedFileInfo


class FileService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = {'.pdf', '.docx', '.txt'}
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file for type and size"""
        
        # Check file extension
        if not file.filename:
            return False, "Filename is required"
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            return False, f"File type {file_extension} not supported. Allowed types: {', '.join(self.allowed_extensions)}"
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            if file.size > self.max_file_size:
                return False, f"File size {file.size} exceeds maximum allowed size of {self.max_file_size} bytes"
        
        return True, None
    
    def get_file_type(self, filename: str) -> FileType:
        """Determine file type from filename"""
        extension = Path(filename).suffix.lower()
        if extension == '.pdf':
            return FileType.PDF
        elif extension == '.docx':
            return FileType.DOCX
        elif extension == '.txt':
            return FileType.TXT
        else:
            raise ValueError(f"Unsupported file extension: {extension}")
    
    async def save_file(self, file: UploadFile) -> UploadedFileInfo:
        """Save uploaded file to disk and return file info"""
        
        # Validate file first
        is_valid, error_message = self.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{file_id}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        # Read and validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size {file_size} exceeds maximum allowed size of {self.max_file_size} bytes"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save file to disk
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Reset file position for potential future reads
        await file.seek(0)
        
        return UploadedFileInfo(
            filename=unique_filename,
            file_type=self.get_file_type(file.filename),
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream"
        )
    
    def get_file_path(self, filename: str) -> Path:
        """Get full path to uploaded file"""
        return self.upload_dir / filename
    
    def file_exists(self, filename: str) -> bool:
        """Check if file exists"""
        return self.get_file_path(filename).exists()
    
    async def delete_file(self, filename: str) -> bool:
        """Delete uploaded file"""
        file_path = self.get_file_path(filename)
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def get_secure_filename(self, filename: str) -> str:
        """Generate secure filename to prevent directory traversal"""
        # Remove any path components and keep only the filename
        secure_name = Path(filename).name
        # Replace any potentially dangerous characters
        secure_name = "".join(c for c in secure_name if c.isalnum() or c in "._-")
        return secure_name or "unnamed_file"


# Global file service instance
file_service = FileService()