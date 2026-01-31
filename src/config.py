"""Configuration module for codeforces-editorial-finder."""

import threading
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Cache
    cache_ttl_hours: int = Field(
        default=168,  # 7 days
        description="Cache TTL in hours",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # HTTP
    http_retries: int = Field(default=3, description="Number of HTTP retry attempts")
    user_agent: Optional[str] = Field(
        default=None, description="User agent for HTTP requests. If None, will use default app UA"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(
        default=None, description="Log file path (None for stdout only)"
    )

    # LLM (OpenRouter)
    openrouter_api_key: Optional[str] = Field(
        default=None, description="OpenRouter API key for LLM-based editorial detection"
    )
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-haiku",
        description="OpenRouter model to use for editorial detection",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )
    llm_enabled: bool = Field(
        default=True,
        description="Enable LLM-based editorial detection (fallback to regex if disabled or fails)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("log_file")
    @classmethod
    def expand_log_file(cls, v: Optional[str]) -> Optional[str]:
        """Expand ~ in log file path."""
        if v is None:
            return None
        return str(Path(v).expanduser())

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


# Singleton instance
_settings: Optional[Settings] = None
_settings_lock = threading.Lock()


def get_settings() -> Settings:
    """Get or create settings singleton instance."""
    global _settings
    if _settings is None:
        with _settings_lock:
            if _settings is None:
                _settings = Settings()
    assert _settings is not None
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    with _settings_lock:
        _settings = None
