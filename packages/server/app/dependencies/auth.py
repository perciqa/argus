"""FastAPI dependency for API key validation on ingestion endpoints."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import ARGUS_API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(api_key_header)) -> str | None:
    """Validate X-API-Key header. Skips validation if ARGUS_API_KEY is unset."""
    if not ARGUS_API_KEY:
        return None
    if not secrets.compare_digest(api_key or "", ARGUS_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
