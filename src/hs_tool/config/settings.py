"""
Settings Configuration

Pydantic-based settings management with environment variable support.
Uses pydantic-settings for validation and type conversion.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Connection settings
    database_path: Path = Field(
        default=Path("00_SYS/ot_local_agent.sqlite"),
        description="Path to SQLite database file",
        validation_alias="DATABASE_PATH"
    )
    
    # SQLite-specific settings
    pragma_foreign_keys: bool = Field(
        default=True,
        description="Enable foreign key constraints in SQLite",
        validation_alias="PRAGMA_FOREIGN_KEYS"
    )
    pragma_journal_mode: str = Field(
        default="WAL",
        description="SQLite journal mode (WAL, DELETE, TRUNCATE, etc.)",
        validation_alias="PRAGMA_JOURNAL_MODE"
    )
    pragma_synchronous: str = Field(
        default="NORMAL",
        description="SQLite synchronous mode (OFF, NORMAL, FULL, etc.)",
        validation_alias="PRAGMA_SYNCHRONOUS"
    )
    
    # Connection pool settings (for future expansion)
    max_connections: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of database connections",
        validation_alias="DB_MAX_CONNECTIONS"
    )
    connection_timeout: float = Field(
        default=30.0,
        ge=0,
        description="Database connection timeout in seconds",
        validation_alias="DB_CONNECTION_TIMEOUT"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        case_sensitive=False,
        extra="ignore",
    )


class LLMSettings(BaseSettings):
    """LLM (Large Language Model) configuration settings."""
    
    # Provider settings
    default_provider: str = Field(
        default="disabled",
        description="Default LLM provider (disabled, ollama, llama_cpp)",
        validation_alias="LLM_DEFAULT_PROVIDER"
    )
    
    # Ollama settings
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama API base URL",
        validation_alias="OLLAMA_BASE_URL"
    )
    ollama_timeout: float = Field(
        default=30.0,
        ge=0,
        description="Ollama API timeout in seconds",
        validation_alias="OLLAMA_TIMEOUT"
    )
    
    # Model settings
    default_model: Optional[str] = Field(
        default=None,
        description="Default model name",
        validation_alias="LLM_DEFAULT_MODEL"
    )
    allowed_models: List[str] = Field(
        default_factory=list,
        description="List of allowed model names",
        validation_alias="LLM_ALLOWED_MODELS"
    )
    
    # Safety settings
    pii_redaction_enabled: bool = Field(
        default=True,
        description="Enable PII redaction before LLM calls",
        validation_alias="LLM_PII_REDACTION"
    )
    max_input_tokens: int = Field(
        default=4096,
        ge=1,
        le=32768,
        description="Maximum input tokens for LLM",
        validation_alias="LLM_MAX_INPUT_TOKENS"
    )
    max_output_tokens: int = Field(
        default=1024,
        ge=1,
        le=8192,
        description="Maximum output tokens from LLM",
        validation_alias="LLM_MAX_OUTPUT_TOKENS"
    )
    
    # Local model paths
    models_directory: Path = Field(
        default=Path("models"),
        description="Directory for local LLM models",
        validation_alias="LLM_MODELS_DIR"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        case_sensitive=False,
        extra="ignore",
    )


class PathSettings(BaseSettings):
    """File path configuration settings."""
    
    # Base paths
    project_root: Path = Field(
        default=Path.cwd(),
        description="Project root directory",
        validation_alias="PROJECT_ROOT"
    )
    data_directory: Path = Field(
        default=Path("00_SYS"),
        description="Data directory for databases, backups, etc.",
        validation_alias="DATA_DIR"
    )
    
    # Backup settings
    backup_directory: Path = Field(
        default=Path("00_SYS/backups"),
        description="Backup directory",
        validation_alias="BACKUP_DIR"
    )
    max_backups: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of backups to keep",
        validation_alias="MAX_BACKUPS"
    )
    backup_compression: bool = Field(
        default=True,
        description="Compress backup files",
        validation_alias="BACKUP_COMPRESS"
    )
    
    # Log settings
    log_directory: Path = Field(
        default=Path("00_SYS/logs"),
        description="Log directory",
        validation_alias="LOG_DIR"
    )
    log_level: str = Field(
        default="INFO",
        description="Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="LOG_LEVEL"
    )
    audit_log_enabled: bool = Field(
        default=True,
        description="Enable audit logging",
        validation_alias="AUDIT_LOG_ENABLED"
    )
    
    # Config file path
    config_path: Path = Field(
        default=Path("00_SYS/config/app_settings.yaml"),
        description="Path to configuration file",
        validation_alias="CONFIG_PATH"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="PATH_",
        case_sensitive=False,
        extra="ignore",
    )


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    # Password hashing
    password_hash_algorithm: str = Field(
        default="argon2id",
        description="Password hashing algorithm (argon2id, bcrypt, scrypt)",
        validation_alias="PASSWORD_HASH_ALGO"
    )
    password_hash_rounds: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Password hash rounds (for Argon2)",
        validation_alias="PASSWORD_HASH_ROUNDS"
    )
    password_hash_memory: int = Field(
        default=65536,
        ge=1024,
        description="Password hash memory in KB (for Argon2)",
        validation_alias="PASSWORD_HASH_MEMORY"
    )
    password_hash_parallelism: int = Field(
        default=4,
        ge=1,
        description="Password hash parallelism (for Argon2)",
        validation_alias="PASSWORD_HASH_PARALLELISM"
    )
    
    # Session settings
    session_secret: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Session secret key",
        validation_alias="SESSION_SECRET"
    )
    session_timeout_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Session timeout in hours",
        validation_alias="SESSION_TIMEOUT_HOURS"
    )
    
    # CSRF protection
    csrf_enabled: bool = Field(
        default=True,
        description="Enable CSRF protection",
        validation_alias="CSRF_ENABLED"
    )
    csrf_secret: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="CSRF secret key",
        validation_alias="CSRF_SECRET"
    )
    
    # Authentication
    auth_required: bool = Field(
        default=True,
        description="Require authentication",
        validation_alias="AUTH_REQUIRED"
    )
    max_login_attempts: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum login attempts before lockout",
        validation_alias="MAX_LOGIN_ATTEMPTS"
    )
    login_lockout_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Login lockout duration in minutes",
        validation_alias="LOGIN_LOCKOUT_MINUTES"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        case_sensitive=False,
        extra="ignore",
    )


class AppSettings(BaseSettings):
    """Main application settings."""
    
    # Application info
    app_name: str = Field(
        default="H-S-Tool",
        description="Application name",
        validation_alias="APP_NAME"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
        validation_alias="APP_VERSION"
    )
    app_environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)",
        validation_alias="APP_ENVIRONMENT"
    )
    
    # Server settings
    host: str = Field(
        default="127.0.0.1",
        description="Server host",
        validation_alias="HOST"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
        validation_alias="PORT"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        validation_alias="DEBUG"
    )
    
    # License settings
    license_required: bool = Field(
        default=True,
        description="Require license file",
        validation_alias="LICENSE_REQUIRED"
    )
    license_file_path: Path = Field(
        default=Path("00_SYS/license/license.json"),
        description="Path to license file",
        validation_alias="LICENSE_FILE_PATH"
    )
    demo_mode_allowed: bool = Field(
        default=True,
        description="Allow demo mode without license",
        validation_alias="DEMO_MODE_ALLOWED"
    )
    
    # Feature flags
    features: Dict[str, bool] = Field(
        default_factory=dict,
        description="Feature flags",
        validation_alias="FEATURES"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """
    Main settings class that aggregates all configuration.
    
    Settings are loaded in the following priority order:
    1. Environment variables
    2. Configuration file (YAML)
    3. Default values
    
    Usage:
        from hs_tool.config import Settings, load_settings
        
        # Get settings (cached)
        settings = Settings()
        
        # Or load from file
        settings = load_settings()
    """
    
    # Sub-settings
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    # Additional metadata
    config_file_loaded: bool = False
    config_file_path: Optional[Path] = None
    
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )
    
    @field_validator('app', mode='before')
    @classmethod
    def validate_app(cls, v: Any) -> AppSettings:
        if isinstance(v, dict):
            return AppSettings(**v)
        return v
    
    @field_validator('database', mode='before')
    @classmethod
    def validate_database(cls, v: Any) -> DatabaseSettings:
        if isinstance(v, dict):
            return DatabaseSettings(**v)
        return v
    
    @field_validator('llm', mode='before')
    @classmethod
    def validate_llm(cls, v: Any) -> LLMSettings:
        if isinstance(v, dict):
            return LLMSettings(**v)
        return v
    
    @field_validator('paths', mode='before')
    @classmethod
    def validate_paths(cls, v: Any) -> PathSettings:
        if isinstance(v, dict):
            return PathSettings(**v)
        return v
    
    @field_validator('security', mode='before')
    @classmethod
    def validate_security(cls, v: Any) -> SecuritySettings:
        if isinstance(v, dict):
            return SecuritySettings(**v)
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings instance (cached).
    
    This function caches the settings instance for performance.
    Call `clear_settings_cache()` to reload settings.
    """
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache, forcing a reload on next access."""
    get_settings.cache_clear()
