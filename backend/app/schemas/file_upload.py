from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict
from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    upload_path: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class FileValidationError(BaseModel):
    error: str
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UploadedFileInfo(BaseModel):
    filename: str
    file_type: FileType
    file_size: int
    content_type: str
    
    @field_validator('file_type', mode='before')
    def validate_file_type(cls, v, info):
        filename = info.data.get('filename', '')
        if filename:
            extension = filename.lower().split('.')[-1]
            if extension not in ['pdf', 'docx', 'txt']:
                raise ValueError(f"Unsupported file type: {extension}")
            return extension
        return v

    model_config = ConfigDict(from_attributes=True)