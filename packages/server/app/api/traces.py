"""Trace ingestion and retrieval endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.db import repository as repo
from app.schemas import TraceIn, TraceDetail, TraceListResponse, TraceSummary
from app.ws.manager import ws_manager

logger = logging.getLogger("argus.api.traces")
router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", status_code=201)
async def ingest_trace(
    trace: TraceIn,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Ingest a completed trace from the Argus SDK.

    Persists header + all spans to SQLite, broadcasts new_trace via
    WebSocket, then fires the eval engine as a background task.
    """
    payload = trace.model_dump(mode="json")

    try:
        await repo.upsert_trace(payload)
    except Exception as exc:
        logger.error("Failed to persist trace %s: %s", trace.trace_id, exc)
        raise HTTPException(status_code=500, detail="Failed to persist trace") from exc

    # Broadcast to dashboard immediately
    background_tasks.add_task(
        ws_manager.broadcast,
        "new_trace",
        {
            "trace_id":       trace.trace_id,
            "agent_name":     trace.agent_name,
            "task":           trace.task,
            "status":         trace.status.value,
            "total_cost_usd": trace.total_cost_usd,
            "total_tokens":   trace.total_tokens,
            "duration_ms":    trace.duration_ms,
        },
    )

    # Fire eval engine (non-blocking)
    from app.eval.engine import evaluate_trace
    background_tasks.add_task(evaluate_trace, trace.trace_id)

    return {"trace_id": trace.trace_id, "status": "accepted"}


@router.get("", response_model=TraceListResponse)
async def list_traces(
    limit:      int           = Query(50, ge=1, le=200),
    offset:     int           = Query(0, ge=0),
    agent_name: Optional[str] = Query(None),
    status:     Optional[str] = Query(None),
) -> TraceListResponse:
    """List traces, most recent first. Supports filtering and pagination."""
    rows, total = await repo.list_traces(
        limit=limit,
        offset=offset,
        agent_name=agent_name,
        status=status,
    )
    return TraceListResponse(
        traces=[TraceSummary(**r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: str) -> TraceDetail:
    """Return a single trace with its full span tree."""
    row = await repo.get_trace_detail(trace_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return TraceDetail(**row)
