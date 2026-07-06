"""Eval results endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.db import repository as repo
from app.schemas import EvalListResponse, EvalSummary

router = APIRouter(prefix="/evals", tags=["evals"])


@router.get("", response_model=EvalListResponse)
async def list_evals(
    limit:  int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> EvalListResponse:
    """List eval results, most recent first."""
    rows, total = await repo.list_evals(limit=limit, offset=offset)

    scores = [r["overall_score"] for r in rows if r.get("overall_score") is not None]
    pass_count = sum(1 for r in rows if r.get("verdict") == "pass")

    return EvalListResponse(
        evals=[EvalSummary(**r) for r in rows],
        total=total,
        avg_score=round(sum(scores) / len(scores), 1) if scores else None,
        pass_rate=round(pass_count / len(rows), 3) if rows else None,
    )


@router.get("/scores")
async def get_scores(
    days: int = Query(7, ge=1, le=90),
) -> list[dict]:
    """Daily average eval scores for the last N days — used for the drift chart."""
    return await repo.get_eval_scores(days=days)


@router.get("/{eval_id}")
async def get_eval(eval_id: str) -> dict:
    """Return a single eval result."""
    from app.db.repository import get_db
    async with await get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM eval_results WHERE eval_id = ?", [eval_id]
        )
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Eval {eval_id} not found")
    return dict(rows[0])
