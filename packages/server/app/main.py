"""
Argus Server — FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.api import traces, finops, evals, health
from app.ws.manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and background tasks on startup."""
    await init_db()
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Argus by Perciqa",
    description="Agent reliability engine — trace, evaluate, and optimize your AI agents.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten post-hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api")
app.include_router(traces.router, prefix="/api")
app.include_router(finops.router, prefix="/api")
app.include_router(evals.router, prefix="/api")

# WebSocket
app.include_router(ws_manager.router)
