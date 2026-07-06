"""Eval results endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/evals", tags=["evals"])


@router.get("")
async def list_evals():
    # TODO: Day 2 — list eval results
    raise NotImplementedError


@router.get("/scores")
async def get_scores():
    # TODO: Day 2 — score timeseries for drift chart
    raise NotImplementedError


@router.get("/{eval_id}")
async def get_eval(eval_id: str):
    # TODO: Day 2 — single eval detail
    raise NotImplementedError
