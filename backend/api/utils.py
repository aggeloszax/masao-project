from __future__ import annotations

import hashlib


def device_log_hash(device_id: str) -> str:
    """Return a short stable hash for anonymous device ids in logs.

    Args:
        device_id: Raw anonymous frontend device id.

    Returns:
        str: First 12 hex characters of the SHA-256 digest.

    Raises:
        None.
    """
    return hashlib.sha256(device_id.encode("utf-8")).hexdigest()[:12]
