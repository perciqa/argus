"""Central server configuration — reads from environment."""

import os


ARGUS_API_KEY: str = os.getenv("ARGUS_API_KEY", "")

ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]
