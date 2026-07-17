import pytest
from pydantic import ValidationError

from api.config import Settings


def test_production_settings_reject_default_internal_api_key() -> None:
    with pytest.raises(ValidationError, match="INTERNAL_API_KEY"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres",
            chat_rate_limit_backend="redis",
            redis_url="rediss://user:pass@redis.render.com:6379/0",
            cors_allowed_origins=["https://masao.onrender.com"],
            internal_api_key="change-this",
        )


def test_production_settings_reject_memory_rate_limiter() -> None:
    with pytest.raises(ValidationError, match="RATE_LIMIT_BACKEND=redis"):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres",
            chat_rate_limit_backend="memory",
            redis_url="rediss://user:pass@redis.render.com:6379/0",
            cors_allowed_origins=["https://masao.onrender.com"],
            internal_api_key="super-secret-api-key",
        )


def test_production_settings_accept_render_supabase_redis_values() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres",
        chat_rate_limit_backend="redis",
        redis_url="rediss://user:pass@redis.render.com:6379/0",
        cors_allowed_origins=["https://masao.onrender.com"],
        internal_api_key="super-secret-api-key",
    )

    assert settings.environment == "production"
    assert settings.chat_rate_limit_backend == "redis"
    assert settings.redis_url == "rediss://user:pass@redis.render.com:6379/0"


def test_cors_origins_accept_comma_separated_render_env_value() -> None:
    settings = Settings(
        cors_allowed_origins="https://masao.onrender.com, https://masao.vercel.app",
    )

    assert settings.cors_allowed_origins == ["https://masao.onrender.com", "https://masao.vercel.app"]


def test_chat_retention_days_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="chat_retention_days"):
        Settings(chat_retention_days=0)


def test_chat_ip_rate_limit_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="chat_ip_rate_limit_requests"):
        Settings(chat_ip_rate_limit_requests=0)
