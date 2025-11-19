from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import aiofiles
from pathlib import Path

from app.core.deps import get_db, get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactResponse
from app.repositories.contact import ContactRepository

router = APIRouter()


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    email: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new contact submission with optional image upload
    Only accepts image files (png, jpeg, jpg)
    Images are saved to the uploads folder and only the filename is stored in the database
    """
    # Validate and save file if provided
    image_filename = None
    if file:
        # Check file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed (PNG, JPEG, JPG)"
            )
        
        # Check file extension
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
        if file_extension not in ['png', 'jpeg', 'jpg']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PNG, JPEG, and JPG image files are allowed"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower() if file.filename else '.jpg'
        unique_filename = f"{file_id}{file_extension}"
        
        # Ensure upload directory exists
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        
        # Save file to disk
        file_path = upload_dir / unique_filename
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            image_filename = unique_filename
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save image file: {str(e)}"
            )
    
    # Create contact submission
    contact_data = ContactCreate(
        email=email,
        description=description,
        image_data=image_filename  # Store only the filename, not base64
    )
    
    repo = ContactRepository(db)
    contact = await repo.create(contact_data, current_user.id)
    
    return ContactResponse.model_validate(contact)


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all contact submissions (for the current user)
    """
    repo = ContactRepository(db)
    contacts = await repo.get_by_user_id(current_user.id, limit=limit)
    return [ContactResponse.model_validate(contact) for contact in contacts]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific contact submission by ID
    """
    from uuid import UUID
    try:
        contact_uuid = UUID(contact_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contact ID format"
        )
    
    repo = ContactRepository(db)
    contact = await repo.get_by_id(contact_uuid)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Only allow users to view their own contacts
    if contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this contact"
        )
    
    return ContactResponse.model_validate(contact)

