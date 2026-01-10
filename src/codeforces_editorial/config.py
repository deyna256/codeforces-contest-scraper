"""Configuration module for codeforces-editorial-finder."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI API
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")

    # Cache
    cache_dir: str = Field(
        default="~/.cache/codeforces-editorial", description="Directory for cache storage"
    )
    cache_ttl_hours: int = Field(
        default=168,  # 7 days
        description="Cache TTL in hours",
    )

    # HTTP
    http_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    http_retries: int = Field(default=3, description="Number of HTTP retry attempts")
    http_js_wait: int = Field(
        default=5000, description="Time to wait for JS content to load (milliseconds)"
    )
    user_agent: str = Field(
        default="codeforces-editorial-finder/1.0", description="User agent for HTTP requests"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(
        default=None, description="Log file path (None for stdout only)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("cache_dir")
    @classmethod
    def expand_cache_dir(cls, v: str) -> str:
        """Expand ~ in cache directory path."""
        return str(Path(v).expanduser())

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

    def get_cache_path(self) -> Path:
        """Get cache directory as Path object, creating it if needed."""
        cache_path = Path(self.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    _settings = None
