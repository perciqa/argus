"""Config endpoint — expose server settings to the dashboard."""

from fastapi import APIRouter, Depends

from app.config import get_argus_api_key
from app.dependencies.auth import require_api_key

router = APIRouter(tags=["config"])


@router.get("/config")
async def server_config(_: str | None = Depends(require_api_key)):
    """Return server configuration visible to the dashboard."""
    return {"api_key": get_argus_api_key()}
