from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.deps import get_current_active_user
from app.repositories.user import UserRepository
from app.repositories.company import CompanyRepository
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    UserCreate, 
    UserResponse,
    Token
)
from app.models.user import User

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    user_repo = UserRepository(db)
    company_repo = CompanyRepository(db)
    
    # Check if user already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Handle company creation or assignment
    company_id = None
    if user_data.company_name:
        # Check if company exists
        company = await company_repo.get_by_name(user_data.company_name)
        if not company:
            # Create new company
            company = await company_repo.create(user_data.company_name)
        company_id = company.id
    
    # Create new user
    try:
        user = await user_repo.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
            company_id=company_id
        )
        return UserResponse.from_orm(user)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        import traceback
        error_details = f"Error creating user: {str(e)}\n{traceback.format_exc()}"
        print(error_details)  # Log the full error to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login user and return access token
    """
    user_repo = UserRepository(db)
    
    # Authenticate user
    user = await user_repo.authenticate(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Refresh access token for authenticated user
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(current_user.id), expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)


@router.get("/verify")
async def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Verify if token is valid
    """
    return {"valid": True, "user_id": str(current_user.id), "role": current_user.role}