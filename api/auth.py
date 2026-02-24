"""API key authentication middleware."""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Comma-separated list of valid API keys. If not set, auth is disabled (dev mode).
_API_KEYS: Optional[str] = os.environ.get("API_KEYS")


def get_api_keys() -> set:
    if not _API_KEYS:
        return set()
    return {k.strip() for k in _API_KEYS.split(",") if k.strip()}


async def require_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)):
    """Dependency that enforces API key auth.

    If API_KEYS env var is not set, auth is disabled (development mode).
    If set, requests must include a valid X-API-Key header.
    """
    valid_keys = get_api_keys()

    # Dev mode: no keys configured, allow all
    if not valid_keys:
        return None

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return api_key
