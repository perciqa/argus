"""
Argus Server — FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS, ensure_api_key
from app.db.database import init_db
from app.api import traces, finops, evals, health, config
from app.ws.manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and background tasks on startup."""
    await init_db()
    ensure_api_key()
    yield


app = FastAPI(
    title="Argus by Perciqa",
    description="Agent reliability engine — trace, evaluate, and optimize your AI agents.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api")
app.include_router(traces.router, prefix="/api")
app.include_router(finops.router, prefix="/api")
app.include_router(evals.router, prefix="/api")
app.include_router(config.router, prefix="/api")

# WebSocket
app.include_router(ws_manager.router)
