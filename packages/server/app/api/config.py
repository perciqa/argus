"""Config endpoint — expose server settings to the dashboard."""

import secrets

from fastapi import APIRouter

from app.config import get_argus_api_key

router = APIRouter(tags=["config"])


@router.get("/config")
async def server_config():
    """Return server configuration visible to the dashboard."""
    return {"api_key": get_argus_api_key()}
