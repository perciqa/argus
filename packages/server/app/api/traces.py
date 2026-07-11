"""Trace ingestion and retrieval endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request

from app.db import repository as repo
from app.dependencies.auth import require_api_key
from app.limiter import limiter
from app.schemas import TraceIn, TraceDetail, TraceListResponse, TraceSummary
from app.ws.manager import ws_manager

logger = logging.getLogger("argus.api.traces")
router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", status_code=201)
@limiter.limit("60/minute")
async def ingest_trace(
    request: Request,
    trace: TraceIn,
    background_tasks: BackgroundTasks,
    _api_key: str | None = Depends(require_api_key),
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

    # Broadcast cost alert if budget was exceeded
    if trace.status.value == "error" and trace.error_message and (
        "budget" in trace.error_message.lower()
        or "BudgetExceeded" in (trace.error_message or "")
    ):
        background_tasks.add_task(
            ws_manager.broadcast,
            "cost_alert",
            {
                "trace_id":       trace.trace_id,
                "agent_name":     trace.agent_name,
                "actual_cost_usd": trace.total_cost_usd,
                "error_message":  trace.error_message,
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
    _: str | None = Depends(require_api_key),
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
async def get_trace(
    trace_id: str,
    _: str | None = Depends(require_api_key),
) -> TraceDetail:
    """Return a single trace with its full span tree."""
    row = await repo.get_trace_detail(trace_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return TraceDetail(**row)


@router.get("/{trace_id}/replay")
async def replay_trace(
    trace_id: str,
    _: str | None = Depends(require_api_key),
) -> dict:
    """Return ordered span timeline for step-by-step trajectory replay."""
    row = await repo.get_trace_detail(trace_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    # Build ordered flat timeline with step numbers
    spans = row.get("spans", [])
    steps = []
    for i, span in enumerate(
        sorted(spans, key=lambda s: s.get("start_time", ""))
    ):
        steps.append({
            "step":        i + 1,
            "span_id":     span.get("span_id"),
            "name":        span.get("name"),
            "kind":        span.get("kind"),
            "status":      span.get("status"),
            "duration_ms": span.get("duration_ms"),
            "parent_span_id": span.get("parent_span_id"),
            "model_call": {
                "model":    span.get("model_name"),
                "provider": span.get("model_provider"),
                "tokens":   span.get("completion_tokens"),
                "cost_usd": span.get("model_cost_usd"),
            } if span.get("model_name") else None,
            "tool_call": {
                "name":  span.get("tool_name"),
                "error": span.get("tool_error"),
            } if span.get("tool_name") else None,
            "error_message": span.get("error_message"),
        })

    return {
        "trace_id":     trace_id,
        "agent_name":   row.get("agent_name"),
        "task":         row.get("task"),
        "total_steps":  len(steps),
        "duration_ms":  row.get("duration_ms"),
        "total_cost_usd": row.get("total_cost_usd"),
        "steps":        steps,
    }
