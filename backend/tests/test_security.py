import logging

import pytest
from fastapi import HTTPException

from api.dependencies import device_log_hash, verify_internal_api_key
from api.routers.chat import log_chat_backend_error


@pytest.mark.asyncio
async def test_verify_internal_api_key_rejects_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.dependencies.settings.internal_api_key", "expected-secret")

    with pytest.raises(HTTPException) as exc_info:
        await verify_internal_api_key("wrong-secret")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_internal_api_key_accepts_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.dependencies.settings.internal_api_key", "expected-secret")

    assert await verify_internal_api_key("expected-secret") == "expected-secret"


def test_device_log_hash_is_stable_and_redacts_raw_device_id() -> None:
    raw_device_id = "device-12345"

    hashed = device_log_hash(raw_device_id)

    assert hashed == device_log_hash(raw_device_id)
    assert raw_device_id not in hashed
    assert len(hashed) == 12


def test_chat_error_logging_uses_device_hash_not_raw_device_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="api.routers.chat")

    log_chat_backend_error(table_number=12, device_id="device-12345")

    assert "device-12345" not in caplog.text
    assert "device_hash=" in caplog.text
