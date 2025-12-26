"""
Application Configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Secure Code Review Bot"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    ENABLE_CACHING: bool = True
    CACHE_TTL_LLM: int = 86400  # 24 hours
    CACHE_TTL_SCAN: int = 3600  # 1 hour
    
    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "secure_code_review"
    
    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2000
    
    # Anthropic
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Google
    GOOGLE_API_KEY: str | None = None
    GOOGLE_MODEL: str = "gemini-1.5-pro"
    
    # LLM Provider Selection
    LLM_PROVIDER: str = "openai"  # openai, anthropic, google, or auto
    LLM_COST_BUDGET_MONTHLY: float = 1000.0  # Monthly budget in USD
    
    # GitHub
    GITHUB_TOKEN: str | None = None
    GITHUB_WEBHOOK_SECRET: str | None = None
    
    # Scanning
    MAX_FILE_SIZE_MB: int = 10
    CLONE_TIMEOUT_SECONDS: int = 300
    SCAN_TIMEOUT_SECONDS: int = 600
    
    # Privacy
    ENABLE_PII_REDACTION: bool = True
    ENABLE_SECRET_REDACTION: bool = True
    
    # Notifications
    SLACK_WEBHOOK_URL: str | None = None
    DISCORD_WEBHOOK_URL: str | None = None
    ENABLE_SLACK_NOTIFICATIONS: bool = False
    ENABLE_DISCORD_NOTIFICATIONS: bool = False
    NOTIFICATION_MIN_SEVERITY: str = "HIGH"  # Only notify for HIGH and CRITICAL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
