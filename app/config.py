"""
Application Configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Secure Code Review Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "secure_code_review"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2000
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # Scanning
    MAX_FILE_SIZE_MB: int = 10
    CLONE_TIMEOUT_SECONDS: int = 300
    SCAN_TIMEOUT_SECONDS: int = 600
    
    # Privacy
    ENABLE_PII_REDACTION: bool = True
    ENABLE_SECRET_REDACTION: bool = True
    
    # Notifications
    SLACK_WEBHOOK_URL: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    ENABLE_SLACK_NOTIFICATIONS: bool = False
    ENABLE_DISCORD_NOTIFICATIONS: bool = False
    NOTIFICATION_MIN_SEVERITY: str = "HIGH"  # Only notify for HIGH and CRITICAL
    
    # Caching (Redis)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    ENABLE_CACHING: bool = True
    CACHE_TTL_LLM: int = 86400  # 24 hours
    CACHE_TTL_SCAN: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
