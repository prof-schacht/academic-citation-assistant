"""Application configuration using Pydantic settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = Field(default="Academic Citation Assistant")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db"
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=0)
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_password: str = Field(default="")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Security
    secret_key: str = Field(default="your-secret-key-here-change-in-production")
    jwt_secret_key: str = Field(default="your-jwt-secret-key-here-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # File Upload
    max_upload_size: int = Field(default=52428800)  # 50MB
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "txt"])
    upload_dir: str = Field(default="./uploads")
    
    # Embeddings
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")


# Create a global settings instance
settings = Settings()