"""Trace ingestion and retrieval endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("")
async def ingest_trace():
    # TODO: Day 1-2 — implement trace ingestion
    raise NotImplementedError


@router.get("")
async def list_traces():
    # TODO: Day 1-2 — implement trace listing
    raise NotImplementedError


@router.get("/{trace_id}")
async def get_trace(trace_id: str):
    # TODO: Day 1-2 — implement trace detail
    raise NotImplementedError
