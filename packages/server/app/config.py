"""Central server configuration — reads from environment."""

import os
import secrets
import logging

logger = logging.getLogger("argus.config")

_key: str | None = None


def get_argus_api_key() -> str:
    """Return the configured API key. Auto-generates a demo key at startup if none is set."""
    global _key
    if _key is not None:
        return _key
    _key = os.getenv("ARGUS_API_KEY", "")
    if not _key:
        _key = f"arg_{secrets.token_urlsafe(24).rstrip('=')}"
        os.environ["ARGUS_API_KEY"] = _key
        logger.info("No ARGUS_API_KEY set — generated demo key: %s", _key)
    return _key


ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]
