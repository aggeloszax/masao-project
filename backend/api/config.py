from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"

load_dotenv(ROOT_DIR / ".env")


def _read_yaml() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


_yaml_config = _read_yaml()


def _parse_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_csv(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [part.strip() for part in value.split(",") if part.strip()]


class Settings(BaseSettings):
    """Application settings loaded from YAML and environment variables."""

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    app_name: str = Field(default=_yaml_config.get("app", {}).get("name", "Masao Restaurant Chatbot API"))
    app_version: str = Field(default=_yaml_config.get("app", {}).get("version", "1.0.0"))
    environment: str = Field(default=os.getenv("ENVIRONMENT", _yaml_config.get("app", {}).get("environment", "development")))

    restaurant_slug: str = Field(default=_yaml_config.get("restaurant", {}).get("slug", "masao"))
    restaurant_display_name: str = Field(default=_yaml_config.get("restaurant", {}).get("display_name", "Masao"))

    database_url: str = Field(default=os.getenv("DATABASE_URL", _yaml_config.get("database", {}).get("url")))
    database_pool_size: int = Field(default=_yaml_config.get("database", {}).get("pool_size", 10))
    database_max_overflow: int = Field(default=_yaml_config.get("database", {}).get("max_overflow", 20))
    database_pool_timeout_seconds: int = Field(default=_yaml_config.get("database", {}).get("pool_timeout_seconds", 30))

    cors_allowed_origins: list[str] = Field(
        default=os.getenv(
            "CORS_ALLOWED_ORIGINS",
            _yaml_config.get("cors", {}).get("allowed_origins", []),
        )
    )
    cors_allowed_methods: list[str] = Field(
        default=os.getenv(
            "CORS_ALLOWED_METHODS",
            _yaml_config.get("cors", {}).get("allowed_methods", ["GET", "POST", "OPTIONS"]),
        )
    )

    chat_history_limit: int = Field(default=_yaml_config.get("chat", {}).get("history_limit", 20))
    chat_max_user_message_chars: int = Field(default=_yaml_config.get("chat", {}).get("max_user_message_chars", 1000))
    chat_default_table_number: int = Field(default=_yaml_config.get("chat", {}).get("default_table_number", 1))

    chat_rate_limit_requests: int = Field(default=_yaml_config.get("rate_limit", {}).get("chat_requests", 20), gt=0)
    chat_rate_limit_window_seconds: int = Field(default=_yaml_config.get("rate_limit", {}).get("window_seconds", 60), gt=0)
    chat_rate_limit_max_buckets: int = Field(default=_yaml_config.get("rate_limit", {}).get("max_buckets", 5000), gt=0)
    chat_rate_limit_backend: str = Field(default=os.getenv("RATE_LIMIT_BACKEND", _yaml_config.get("rate_limit", {}).get("backend", "memory")))
    redis_url: str | None = Field(default=os.getenv("REDIS_URL", _yaml_config.get("rate_limit", {}).get("redis_url")))
    redis_key_prefix: str = Field(default=os.getenv("REDIS_KEY_PREFIX", _yaml_config.get("rate_limit", {}).get("redis_key_prefix", "masao")))
    redis_socket_timeout_seconds: float = Field(
        default=float(
            os.getenv(
                "REDIS_SOCKET_TIMEOUT_SECONDS",
                _yaml_config.get("rate_limit", {}).get("redis_socket_timeout_seconds", 1.0),
            )
        ),
        gt=0,
    )
    rate_limit_fail_closed: bool = Field(
        default=_parse_bool(os.getenv("RATE_LIMIT_FAIL_CLOSED"), _yaml_config.get("rate_limit", {}).get("fail_closed", True))
    )

    internal_api_key: str = Field(default=os.getenv("INTERNAL_API_KEY", "change-this-for-internal-admin-endpoints"))

    anthropic_api_key: str | None = Field(default=os.getenv("ANTHROPIC_API_KEY", _yaml_config.get("ai", {}).get("api_key")))
    anthropic_model: str = Field(default=os.getenv("ANTHROPIC_MODEL", _yaml_config.get("ai", {}).get("model", "claude-opus-4-8")))
    anthropic_max_tokens: int = Field(default=int(os.getenv("ANTHROPIC_MAX_TOKENS", _yaml_config.get("ai", {}).get("max_tokens", 1024))), gt=0)
    anthropic_timeout_seconds: float = Field(
        default=float(
            os.getenv(
                "ANTHROPIC_TIMEOUT_SECONDS",
                _yaml_config.get("ai", {}).get("timeout_seconds", 60.0),
            )
        ),
        gt=0,
    )

    @field_validator("environment", "chat_rate_limit_backend")
    @classmethod
    def normalize_lower_text(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("cors_allowed_origins", "cors_allowed_methods", mode="before")
    @classmethod
    def parse_csv_list(cls, value: str | list[str] | None) -> list[str]:
        return _parse_csv(value)

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Fail fast on unsafe production configuration.

        Args:
            None.

        Returns:
            Settings: Validated settings.

        Raises:
            ValueError: If production settings are unsafe or incomplete.
        """
        if self.environment != "production":
            return self

        errors: list[str] = []
        unsafe_api_keys = {"", "change-this", "change-this-for-internal-admin-endpoints"}
        if self.internal_api_key.strip() in unsafe_api_keys:
            errors.append("INTERNAL_API_KEY must be a non-default secret in production")
        if not self.database_url:
            errors.append("DATABASE_URL is required in production")
        if self.chat_rate_limit_backend != "redis":
            errors.append("RATE_LIMIT_BACKEND=redis is required in production")
        if not self.redis_url:
            errors.append("REDIS_URL is required when RATE_LIMIT_BACKEND=redis in production")
        if "*" in self.cors_allowed_origins:
            errors.append("CORS_ALLOWED_ORIGINS cannot contain '*' in production")

        external_origins = [
            origin
            for origin in self.cors_allowed_origins
            if not origin.startswith("http://localhost") and not origin.startswith("http://127.0.0.1")
        ]
        if not external_origins:
            errors.append("CORS_ALLOWED_ORIGINS must include a production Render/frontend origin")

        if errors:
            raise ValueError("; ".join(errors))
        return self


settings = Settings()
