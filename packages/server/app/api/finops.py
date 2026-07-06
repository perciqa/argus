"""FinOps cost aggregation endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/finops", tags=["finops"])


@router.get("/summary")
async def get_summary():
    # TODO: Day 1-2 — aggregate cost summary
    raise NotImplementedError


@router.get("/timeseries")
async def get_timeseries():
    # TODO: Day 1-2 — cost over time
    raise NotImplementedError


@router.get("/breakdown")
async def get_breakdown():
    # TODO: Day 1-2 — cost by model and provider
    raise NotImplementedError
