# src\core\config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, Field, field_validator, SecretStr
from typing import Optional
from functools import lru_cache
class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str
   
    # Application settings
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
   
    # Authentication settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, ge=5, le=60)
   
    # Email settings
    EMAIL_SENDER: EmailStr
    EMAIL_PASSWORD: SecretStr
    FRONTEND_URL: str
   
    # Google settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_SEARCH_CONSOLE_REDIRECT_URI: str
    GOOGLE_ANALYTICS_REDIRECT_URI: str
    GOOGLE_REDIRECT_URI: str
    API_KEY: str
    
    # Security settings
    MAX_LOGIN_ATTEMPTS: int = Field(5, ge=3, le=10)
    LOGIN_ATTEMPT_WINDOW: int = Field(15, ge=5, le=30)
    PASSWORD_RESET_TOKEN_EXPIRE: int = Field(60, ge=15, le=120)
    @field_validator('ENVIRONMENT')
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting"""
        allowed = {'development', 'testing', 'production'}
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {", ".join(allowed)}')
        return v

    @field_validator('FRONTEND_URL')
    def validate_frontend_url(cls, v: str) -> str:
        """Validate frontend URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Frontend URL must start with http:// or https://')
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()

# Create settings instance
settings = get_settings()