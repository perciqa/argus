"""Eval engine — LLM-as-judge using Gemma."""

# TODO: Day 2 — implement eval engine
# Responsibilities:
# - Accept a Trace object
# - Format trajectory as JSON for the judge prompt
# - Call Gemma (local AMD or Fireworks) with the judge prompt
# - Parse structured JSON response into an EvalResult
# - Persist to eval_results table
# - Broadcast eval_complete via WebSocket


async def evaluate_trace(trace_id: str) -> None:
    """Evaluate a trace using the Gemma judge. Runs as a background task."""
    raise NotImplementedError
