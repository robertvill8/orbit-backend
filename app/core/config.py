"""
Configuration management using Pydantic Settings.
All environment variables are validated and typed here.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="AI Agent Cockpit Backend", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")
    reload: bool = Field(default=False, alias="RELOAD")

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://agent_user:agent_pass@localhost:5432/agent_cockpit",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    session_ttl_seconds: int = Field(default=86400, alias="SESSION_TTL_SECONDS")
    message_cache_ttl_seconds: int = Field(default=3600, alias="MESSAGE_CACHE_TTL_SECONDS")

    # LLM Provider Settings
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")

    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL"
    )
    anthropic_max_tokens: int = Field(default=4096, alias="ANTHROPIC_MAX_TOKENS")

    # N8N Integration
    n8n_base_url: str = Field(
        default="https://n8n-wsex.sliplane.app", alias="N8N_BASE_URL"
    )
    n8n_webhook_email_read: str = Field(
        default="/webhook/email-read", alias="N8N_WEBHOOK_EMAIL_READ"
    )
    n8n_webhook_calendar_create: str = Field(
        default="/webhook/calendar-create", alias="N8N_WEBHOOK_CALENDAR_CREATE"
    )
    n8n_webhook_ocr_process: str = Field(
        default="/webhook/ocr-process", alias="N8N_WEBHOOK_OCR_PROCESS"
    )
    n8n_api_key: Optional[str] = Field(default=None, alias="N8N_API_KEY")
    n8n_timeout_seconds: int = Field(default=30, alias="N8N_TIMEOUT_SECONDS")
    n8n_max_retries: int = Field(default=3, alias="N8N_MAX_RETRIES")

    # Authentication & Security
    secret_key: str = Field(
        default="your-secret-key-min-32-chars-random-please-change-in-production",
        alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=10080, alias="JWT_EXPIRE_MINUTES")

    # Add refresh token expiry for proper JWT auth
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000", alias="CORS_ORIGINS"
    )

    @property
    def ALGORITHM(self) -> str:
        """Alias for jwt_algorithm for compatibility with security module."""
        return self.jwt_algorithm

    @property
    def SECRET_KEY(self) -> str:
        """Alias for secret_key for compatibility with security module."""
        return self.secret_key

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """Alias for access_token_expire_minutes for compatibility."""
        return self.access_token_expire_minutes

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        """Alias for refresh_token_expire_days for compatibility."""
        return self.refresh_token_expire_days

    @property
    def APP_DEBUG(self) -> bool:
        """Alias for debug for compatibility with database module."""
        return self.debug

    @property
    def DATABASE_URL(self) -> str:
        """Alias for database_url for compatibility."""
        return self.database_url

    @property
    def DATABASE_POOL_SIZE(self) -> int:
        """Alias for database_pool_size for compatibility."""
        return self.database_pool_size

    @property
    def DATABASE_MAX_OVERFLOW(self) -> int:
        """Alias for database_max_overflow for compatibility."""
        return self.database_max_overflow

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_burst: int = Field(default=20, alias="RATE_LIMIT_BURST")

    # Monitoring & Observability
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(
        default=0.1, alias="SENTRY_TRACES_SAMPLE_RATE"
    )
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")

    # WebSocket Configuration
    ws_heartbeat_interval: int = Field(
        default=30, alias="WS_HEARTBEAT_INTERVAL", description="WebSocket heartbeat interval in seconds"
    )
    ws_max_connections_per_session: int = Field(
        default=5, alias="WS_MAX_CONNECTIONS_PER_SESSION", description="Maximum WebSocket connections per session"
    )
    ws_connection_timeout: int = Field(
        default=300, alias="WS_CONNECTION_TIMEOUT", description="WebSocket connection timeout in seconds"
    )

    # Feature Flags
    feature_voice_input: bool = Field(default=True, alias="FEATURE_VOICE_INPUT")
    feature_proactive_notifications: bool = Field(
        default=True, alias="FEATURE_PROACTIVE_NOTIFICATIONS"
    )
    feature_background_tasks: bool = Field(
        default=False, alias="FEATURE_BACKGROUND_TASKS"
    )

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Ensure DATABASE_URL uses asyncpg driver for async SQLAlchemy.
        Railway provides postgresql:// URLs which default to psycopg2 (sync).
        This validator transforms them to postgresql+asyncpg:// for async compatibility.
        """
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            # Transform postgresql:// to postgresql+asyncpg://
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the expected values."""
        valid_envs = ["development", "staging", "production", "test"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v_lower

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            return self.parse_cors_origins(self.cors_origins)
        return self.cors_origins


# Global settings instance
settings = Settings()
