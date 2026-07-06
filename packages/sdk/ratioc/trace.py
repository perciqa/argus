"""
Argus SDK — @argus.trace decorator and context manager.

Captures agent function calls as structured spans using Python's
contextvars for correct propagation across async/await boundaries.
"""

from __future__ import annotations

import asyncio
import contextvars
import functools
import inspect
import json
import logging
from typing import Any, Callable, Optional

from ratioc.models import Span, SpanKind, SpanStatus, Trace

logger = logging.getLogger("argus.trace")

# ---------------------------------------------------------------------------
# Context variables — one per async task / thread
# ---------------------------------------------------------------------------

_current_trace: contextvars.ContextVar[Optional[Trace]] = contextvars.ContextVar(
    "argus_current_trace", default=None
)
_current_span: contextvars.ContextVar[Optional[Span]] = contextvars.ContextVar(
    "argus_current_span", default=None
)


def get_current_trace() -> Optional[Trace]:
    return _current_trace.get()


def get_current_span() -> Optional[Span]:
    return _current_span.get()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _safe_serialize(args: tuple, kwargs: dict) -> Any:
    """Serialize function inputs best-effort — never raises."""
    try:
        data: dict = {}
        if args:
            data["args"] = [_try_json(a) for a in args]
        if kwargs:
            data["kwargs"] = {k: _try_json(v) for k, v in kwargs.items()}
        return data or None
    except Exception:
        return None


def _safe_serialize_output(result: Any) -> Any:
    """Serialize function output best-effort — never raises."""
    return _try_json(result)


def _try_json(value: Any) -> Any:
    """Try to make a value JSON-serializable; fall back to a string."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        pass
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass
    return f"<{type(value).__name__}>"


# ---------------------------------------------------------------------------
# Budget guard
# ---------------------------------------------------------------------------

class BudgetExceededError(RuntimeError):
    """Raised when a trace exceeds its configured budget cap."""
    pass


def _check_budget(trace: Trace) -> None:
    """Raise BudgetExceededError if the trace has exceeded its cost cap."""
    from ratioc.config import get_config
    cfg = get_config()
    if cfg.budget_cap_usd is not None and trace.total_cost_usd > cfg.budget_cap_usd:
        raise BudgetExceededError(
            f"Trace {trace.trace_id} exceeded budget cap of "
            f"${cfg.budget_cap_usd:.4f} (current: ${trace.total_cost_usd:.4f})"
        )


# ---------------------------------------------------------------------------
# Core decorator / context manager
# ---------------------------------------------------------------------------

class trace:
    """
    Decorator and context manager for tracing agent functions.

    Usage — decorator:
        @argus.trace(name="search", kind="tool_call")
        def search_web(query: str) -> list[str]:
            ...

        @argus.trace(kind="agent")
        async def my_agent(task: str) -> str:
            ...

    Usage — context manager:
        with argus.trace("parse_intent", kind="reason") as span:
            span.set_attribute("user_query", query)
            result = parse(query)
    """

    def __init__(
        self,
        name: Optional[str] = None,
        kind: str = "internal",
        agent_name: Optional[str] = None,
        task: Optional[str] = None,
    ):
        self.name       = name
        self.kind       = SpanKind(kind)
        self.agent_name = agent_name
        self.task       = task

        # Used when operating as a context manager
        self._span:         Optional[Span]  = None
        self._trace_obj:    Optional[Trace] = None
        self._is_root:      bool            = False
        self._token_trace:  Any             = None
        self._token_span:   Any             = None

    # ------------------------------------------------------------------
    # Decorator usage
    # ------------------------------------------------------------------

    def __call__(self, func: Callable) -> Callable:
        span_name = self.name or func.__name__

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_async(func, span_name, args, kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._execute_sync(func, span_name, args, kwargs)
            return sync_wrapper

    # ------------------------------------------------------------------
    # Sync execution path
    # ------------------------------------------------------------------

    def _execute_sync(self, func: Callable, span_name: str, args: tuple, kwargs: dict) -> Any:
        parent_trace = _current_trace.get()
        parent_span  = _current_span.get()
        is_root      = parent_trace is None

        trace_obj: Optional[Trace] = None
        span:      Optional[Span]  = None
        token_t = token_s = None

        try:
            from ratioc.config import get_config
            cfg = get_config()

            if is_root:
                trace_obj = Trace(
                    agent_name=self.agent_name or cfg.agent_name,
                    task=self.task,
                )
                token_t = _current_trace.set(trace_obj)
            else:
                trace_obj = parent_trace

            span = Span(
                trace_id=trace_obj.trace_id,
                parent_span_id=parent_span.span_id if parent_span else None,
                name=span_name,
                kind=self.kind,
                input_data=_safe_serialize(args, kwargs),
            )
            token_s = _current_span.set(span)
            trace_obj.spans.append(span)

            result = func(*args, **kwargs)

            span.output_data = _safe_serialize_output(result)
            span.status = SpanStatus.OK
            return result

        except BudgetExceededError:
            if span:
                span.status = SpanStatus.ERROR
                span.error_message = "Budget cap exceeded"
                span.error_type = "BudgetExceededError"
            raise

        except Exception as exc:
            if span:
                span.status = SpanStatus.ERROR
                span.error_message = str(exc)
                span.error_type = type(exc).__name__
            raise

        finally:
            if span:
                span.finish()
            if token_s is not None:
                _current_span.reset(token_s)
            if is_root and trace_obj:
                trace_obj.finish()
                if token_t is not None:
                    _current_trace.reset(token_t)
                try:
                    from ratioc.config import get_exporter
                    get_exporter().enqueue(trace_obj)
                except Exception as exc:
                    logger.warning("Failed to enqueue trace: %s", exc)

    # ------------------------------------------------------------------
    # Async execution path
    # ------------------------------------------------------------------

    async def _execute_async(self, func: Callable, span_name: str, args: tuple, kwargs: dict) -> Any:
        parent_trace = _current_trace.get()
        parent_span  = _current_span.get()
        is_root      = parent_trace is None

        trace_obj: Optional[Trace] = None
        span:      Optional[Span]  = None
        token_t = token_s = None

        try:
            from ratioc.config import get_config
            cfg = get_config()

            if is_root:
                trace_obj = Trace(
                    agent_name=self.agent_name or cfg.agent_name,
                    task=self.task,
                )
                token_t = _current_trace.set(trace_obj)
            else:
                trace_obj = parent_trace

            span = Span(
                trace_id=trace_obj.trace_id,
                parent_span_id=parent_span.span_id if parent_span else None,
                name=span_name,
                kind=self.kind,
                input_data=_safe_serialize(args, kwargs),
            )
            token_s = _current_span.set(span)
            trace_obj.spans.append(span)

            result = await func(*args, **kwargs)

            span.output_data = _safe_serialize_output(result)
            span.status = SpanStatus.OK
            return result

        except BudgetExceededError:
            if span:
                span.status = SpanStatus.ERROR
                span.error_message = "Budget cap exceeded"
                span.error_type = "BudgetExceededError"
            raise

        except Exception as exc:
            if span:
                span.status = SpanStatus.ERROR
                span.error_message = str(exc)
                span.error_type = type(exc).__name__
            raise

        finally:
            if span:
                span.finish()
            if token_s is not None:
                _current_span.reset(token_s)
            if is_root and trace_obj:
                trace_obj.finish()
                if token_t is not None:
                    _current_trace.reset(token_t)
                try:
                    from ratioc.config import get_exporter
                    get_exporter().enqueue(trace_obj)
                except Exception as exc:
                    logger.warning("Failed to enqueue trace: %s", exc)

    # ------------------------------------------------------------------
    # Context manager usage  (with argus.trace("name", kind="reason") as span)
    # ------------------------------------------------------------------

    def __enter__(self) -> Span:
        span_name = self.name or "span"
        parent_trace = _current_trace.get()
        parent_span  = _current_span.get()
        self._is_root = parent_trace is None

        from ratioc.config import get_config
        cfg = get_config()

        if self._is_root:
            self._trace_obj = Trace(
                agent_name=self.agent_name or cfg.agent_name,
                task=self.task,
            )
            self._token_trace = _current_trace.set(self._trace_obj)
        else:
            self._trace_obj = parent_trace

        self._span = Span(
            trace_id=self._trace_obj.trace_id,
            parent_span_id=parent_span.span_id if parent_span else None,
            name=span_name,
            kind=self.kind,
        )
        self._token_span = _current_span.set(self._span)
        self._trace_obj.spans.append(self._span)
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._span:
            if exc_type is not None:
                self._span.status = SpanStatus.ERROR
                self._span.error_message = str(exc_val)
                self._span.error_type = exc_type.__name__ if exc_type else None
            self._span.finish()

        if self._token_span is not None:
            _current_span.reset(self._token_span)

        if self._is_root and self._trace_obj:
            self._trace_obj.finish()
            if self._token_trace is not None:
                _current_trace.reset(self._token_trace)
            try:
                from ratioc.config import get_exporter
                get_exporter().enqueue(self._trace_obj)
            except Exception as exc:
                logger.warning("Failed to enqueue trace: %s", exc)

        return False  # Never suppress exceptions


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def start_trace(name: str, task: Optional[str] = None, agent_name: Optional[str] = None) -> "trace":
    """Context manager that starts a new root trace."""
    return trace(name=name, kind="agent", task=task, agent_name=agent_name)


def start_span(name: str, kind: str = "internal") -> "trace":
    """Context manager that starts a child span within the current trace."""
    return trace(name=name, kind=kind)
