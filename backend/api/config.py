from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import Field
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

    cors_allowed_origins: list[str] = Field(default=_yaml_config.get("cors", {}).get("allowed_origins", []))
    cors_allowed_methods: list[str] = Field(default=_yaml_config.get("cors", {}).get("allowed_methods", ["GET", "POST", "OPTIONS"]))

    chat_history_limit: int = Field(default=_yaml_config.get("chat", {}).get("history_limit", 20))
    chat_max_user_message_chars: int = Field(default=_yaml_config.get("chat", {}).get("max_user_message_chars", 1000))
    chat_default_table_number: int = Field(default=_yaml_config.get("chat", {}).get("default_table_number", 1))

    internal_api_key: str = Field(default=os.getenv("INTERNAL_API_KEY", "change-this-for-internal-admin-endpoints"))


settings = Settings()
