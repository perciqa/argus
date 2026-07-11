"""FinOps cost aggregation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.db import repository as repo
from app.dependencies.auth import require_api_key
from app.schemas import FinOpsSummary, TimeseriesPoint

router = APIRouter(prefix="/finops", tags=["finops"])


@router.get("/summary", response_model=FinOpsSummary)
async def get_summary(_: str | None = Depends(require_api_key)) -> FinOpsSummary:
    """
    Return cost summary for today, this week, and all time.

    The key metric: local_tokens always cost $0.00 (AMD inference),
    so savings_usd shows the FinOps value of running locally.
    """
    data = await repo.get_finops_summary()
    return FinOpsSummary(**data)


@router.get("/timeseries")
async def get_timeseries(
    days: int = Query(7, ge=1, le=90),
    _: str | None = Depends(require_api_key),
) -> list[TimeseriesPoint]:
    """Daily cost breakdown for the last N days."""
    rows = await repo.get_finops_timeseries(days=days)
    return [TimeseriesPoint(**r) for r in rows]


@router.get("/breakdown")
async def get_breakdown(_: str | None = Depends(require_api_key)) -> dict:
    """Cost breakdown by agent and by model."""
    return await repo.get_finops_breakdown()
