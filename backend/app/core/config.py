import os
from typing import List, Optional
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file="../.env",  # Look for .env in parent directory (project root)
        case_sensitive=True,
        extra='ignore'
    )
    PROJECT_NAME: str = "Resume Job Matching System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: Optional[str] = "postgresql://neondb_owner:npg_AcJK7NMl2fPn@ep-shiny-sky-adgai6a9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    POSTGRES_SERVER: str = "ep-shiny-sky-adgai6a9-pooler.c-2.us-east-1.aws.neon.tech"
    POSTGRES_USER: str = "neondb_owner"
    POSTGRES_PASSWORD: str = "npg_AcJK7NMl2fPn"
    POSTGRES_DB: str = "neondb"
    POSTGRES_PORT: int = 5432
    
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    # ANTHROPIC_API_KEY: Optional[str] = None
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    @field_validator("DATABASE_URL", mode='before')
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        # If DATABASE_URL provided, use it. Otherwise assemble from parts in info.data
        if isinstance(v, str):
            return v
        data = info.data or {}
        return f"postgresql://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}:{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"

    @field_validator("REDIS_URL", mode='before')
    def assemble_redis_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        data = info.data or {}
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/{data.get('REDIS_DB')}"
    
    # Note: use `model_config = ConfigDict(...)` for pydantic v2; remove `class Config` to avoid conflicts


settings = Settings()