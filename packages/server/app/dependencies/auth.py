"""FastAPI dependency for API key validation on ingestion endpoints."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_argus_api_key

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(api_key_header)) -> str | None:
    """Validate X-API-Key header. Skips validation if ARGUS_API_KEY is unset."""
    stored_key = get_argus_api_key()
    if not stored_key:
        return None
    if not secrets.compare_digest(api_key or "", stored_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
