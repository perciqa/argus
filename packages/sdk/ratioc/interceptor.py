"""
Argus SDK — OpenAI client interceptor.

Monkey-patches openai.OpenAI and openai.AsyncOpenAI to transparently
capture all chat.completions.create() calls — token counts, latency,
cost, and model metadata — without requiring any changes to user code.

Compatible with openai >= 2.0.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from ratioc.models import ModelCall, ModelProvider, Span, SpanKind, SpanStatus

logger = logging.getLogger("argus.interceptor")

_patched = False  # Guard against double-patching


def _detect_provider(base_url: str) -> ModelProvider:
    """Infer the model provider from the API base URL."""
    url = (base_url or "").lower()
    if "fireworks.ai" in url:
        return ModelProvider.FIREWORKS
    if "openai.com" in url:
        return ModelProvider.OPENAI
    if "anthropic.com" in url:
        return ModelProvider.ANTHROPIC
    if any(h in url for h in ("localhost", "127.0.0.1", "0.0.0.0", "amd", "rocm")):
        return ModelProvider.LOCAL
    return ModelProvider.CUSTOM


def _record_model_call(
    base_url: str,
    model: str,
    messages: Any,
    response: Any,
    elapsed_ms: float,
) -> None:
    """Attach a model_call span to the active trace."""
    from ratioc.trace import _current_span, _current_trace
    from ratioc.cost import calculate_cost

    current_span  = _current_span.get()
    current_trace = _current_trace.get()

    if current_trace is None:
        return  # No active trace — skip silently

    provider         = _detect_provider(base_url)
    usage            = getattr(response, "usage", None)
    prompt_tokens    = getattr(usage, "prompt_tokens",     0) or 0
    completion_tokens= getattr(usage, "completion_tokens", 0) or 0
    total_tokens     = getattr(usage, "total_tokens", prompt_tokens + completion_tokens)

    cost = calculate_cost(model, provider, prompt_tokens, completion_tokens)

    # Extract output text best-effort
    output_text: Any = None
    try:
        choices = getattr(response, "choices", None)
        if choices:
            output_text = choices[0].message.content
    except Exception:
        pass

    model_call = ModelCall(
        model=model,
        provider=provider,
        base_url=base_url,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost,
        latency_ms=elapsed_ms,
    )

    model_span = Span(
        trace_id=current_trace.trace_id,
        parent_span_id=current_span.span_id if current_span else None,
        name=model,
        kind=SpanKind.MODEL_CALL,
        status=SpanStatus.OK,
        model_call=model_call,
        input_data=messages,
        output_data=output_text,
    )
    model_span.finish()
    current_trace.spans.append(model_span)

    # Update trace-level cost aggregates immediately so budget guard works
    current_trace.total_tokens    += total_tokens
    current_trace.total_cost_usd  += cost
    current_trace.model_calls_count += 1
    if provider == ModelProvider.LOCAL:
        current_trace.local_tokens  += total_tokens
    else:
        current_trace.cloud_tokens  += total_tokens

    # Check budget after each model call
    from ratioc.trace import _check_budget
    try:
        _check_budget(current_trace)
    except Exception:
        raise  # Re-raise BudgetExceededError so user code can handle it


def patch_openai_client() -> None:
    """
    Monkey-patch openai.OpenAI and openai.AsyncOpenAI to capture all
    chat.completions.create() calls transparently.

    Safe to call multiple times — only patches once.
    """
    global _patched
    if _patched:
        return

    try:
        import openai
        from openai.resources.chat.completions.completions import Completions, AsyncCompletions
    except ImportError:
        logger.warning("openai package not found — interceptor disabled")
        return

    # ----------------------------------------------------------------
    # Sync interceptor
    # ----------------------------------------------------------------
    _original_create = Completions.create

    def _intercepted_create(self, *args, **kwargs):
        start    = time.perf_counter()
        model    = kwargs.get("model", args[0] if args else "unknown")
        messages = kwargs.get("messages", [])
        base_url = str(getattr(self._client, "base_url", "")) if hasattr(self, "_client") else ""

        try:
            response = _original_create(self, *args, **kwargs)
        except Exception:
            raise  # Never suppress API errors

        elapsed_ms = (time.perf_counter() - start) * 1000
        try:
            _record_model_call(base_url, model, messages, response, elapsed_ms)
        except Exception as exc:
            # Budget exceeded — let it propagate
            from ratioc.trace import BudgetExceededError
            if isinstance(exc, BudgetExceededError):
                raise
            logger.debug("Interceptor recording error (non-fatal): %s", exc)

        return response

    Completions.create = _intercepted_create

    # ----------------------------------------------------------------
    # Async interceptor
    # ----------------------------------------------------------------
    _original_async_create = AsyncCompletions.create

    async def _intercepted_async_create(self, *args, **kwargs):
        start    = time.perf_counter()
        model    = kwargs.get("model", args[0] if args else "unknown")
        messages = kwargs.get("messages", [])
        base_url = str(getattr(self._client, "base_url", "")) if hasattr(self, "_client") else ""

        try:
            response = await _original_async_create(self, *args, **kwargs)
        except Exception:
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        try:
            _record_model_call(base_url, model, messages, response, elapsed_ms)
        except Exception as exc:
            from ratioc.trace import BudgetExceededError
            if isinstance(exc, BudgetExceededError):
                raise
            logger.debug("Async interceptor recording error (non-fatal): %s", exc)

        return response

    AsyncCompletions.create = _intercepted_async_create

    _patched = True
    logger.info("Argus: OpenAI client interceptor active")
