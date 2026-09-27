from __future__ import annotations

import hashlib
import secrets
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from libraries.configuration.settings import get_settings
from libraries.logging.logging import get_logger

logger = get_logger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _get_valid_keys() -> dict[str, str]:
    settings = get_settings()
    raw_keys = getattr(settings, "api_keys", "")
    if not raw_keys:
        return {}
    keys = {}
    for raw_key in raw_keys.split(","):
        raw_key = raw_key.strip()
        if raw_key:
            keys[_hash_api_key(raw_key)] = raw_key[:8] + "..."
    return keys


async def verify_api_key(
    request: Request,
    api_key: str | None = Depends(_api_key_header),
) -> str | None:
    settings = get_settings()

    if not settings.is_production:
        return None

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "authentication_required", "detail": "API key required"},
        )

    valid_keys = _get_valid_keys()
    if not valid_keys:
        logger.warning("No API keys configured in production mode")
        return api_key

    key_hash = _hash_api_key(api_key)
    if key_hash not in valid_keys:
        logger.warning(
            "Invalid API key attempt from %s", request.client.host if request.client else "unknown"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_api_key", "detail": "Invalid API key"},
        )

    return api_key


async def optional_api_key(
    request: Request,
    api_key: str | None = Depends(_api_key_header),
) -> str | None:
    settings = get_settings()

    if not settings.is_production:
        return None

    if not api_key:
        return None

    valid_keys = _get_valid_keys()
    if not valid_keys:
        return api_key

    key_hash = _hash_api_key(api_key)
    if key_hash not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_api_key", "detail": "Invalid API key"},
        )

    return api_key
