"""Central server configuration — reads from environment."""

import os


def get_argus_api_key() -> str:
    """Return the configured API key. Returns empty string if auth is disabled."""
    return os.getenv("ARGUS_API_KEY", "")


ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]
