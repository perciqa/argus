"""Central server configuration — reads from environment."""

import os
import secrets
import logging

logger = logging.getLogger("argus.config")


def get_argus_api_key() -> str:
    """Return the configured API key. Returns empty string if auth is disabled."""
    return os.getenv("ARGUS_API_KEY", "")


def ensure_api_key() -> str:
    """Auto-generate a demo key at startup if none is configured."""
    key = os.getenv("ARGUS_API_KEY", "")
    if key:
        return key
    key = f"arg_{secrets.token_urlsafe(24).rstrip('=')}"
    os.environ["ARGUS_API_KEY"] = key
    logger.warning("No ARGUS_API_KEY set — auto-generated a demo key (set ARGUS_API_KEY to persist)")
    return key


ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]
