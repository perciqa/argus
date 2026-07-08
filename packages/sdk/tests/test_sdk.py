"""
SDK tests — trace decorator, cost calculator, and models.
"""

import asyncio
import pytest

import argus
from argus.models import SpanKind, SpanStatus, ModelProvider
from argus.cost import calculate_cost, PRICING_TABLE
from argus.trace import _current_trace, _current_span


# ---------------------------------------------------------------------------
# Cost calculator tests
# ---------------------------------------------------------------------------

class TestCostCalculator:
    def test_local_provider_always_zero(self):
        cost = calculate_cost("any-model", ModelProvider.LOCAL, 1_000_000, 1_000_000)
        assert cost == 0.0

    def test_fireworks_gemma_pricing(self):
        cost = calculate_cost(
            "accounts/fireworks/models/gemma2-9b-it",
            ModelProvider.FIREWORKS,
            1_000_000,  # 1M input tokens
            1_000_000,  # 1M output tokens
        )
        assert cost == pytest.approx(0.10, rel=1e-3)  # $0.05 + $0.05

    def test_unknown_model_uses_default(self):
        cost = calculate_cost("unknown-model-xyz", ModelProvider.FIREWORKS, 1_000_000, 0)
        assert cost == pytest.approx(1.00, rel=1e-3)

    def test_zero_tokens_zero_cost(self):
        cost = calculate_cost("gpt-4o", ModelProvider.OPENAI, 0, 0)
        assert cost == 0.0

    def test_fractional_tokens(self):
        # 100 input tokens at $2.50/1M = $0.00000025
        cost = calculate_cost("gpt-4o", ModelProvider.OPENAI, 100, 0)
        assert cost > 0.0
        assert cost < 0.001


# ---------------------------------------------------------------------------
# Trace decorator — sync
# ---------------------------------------------------------------------------

class TestTraceDecoratorSync:
    def setup_method(self):
        # Reset context between tests
        _current_trace.set(None)
        _current_span.set(None)

    def test_basic_sync_trace(self):
        captured: list = []

        @argus.trace(name="test_func", kind="agent")
        def my_func(x: int) -> int:
            captured.append(_current_trace.get())
            return x * 2

        result = my_func(5)
        assert result == 10
        assert len(captured) == 1

        trace_obj = captured[0]
        assert trace_obj is not None
        assert len(trace_obj.spans) == 1
        assert trace_obj.spans[0].name == "test_func"
        assert trace_obj.spans[0].kind == SpanKind.AGENT

    def test_span_captures_input_output(self):
        @argus.trace(name="add", kind="tool_call")
        def add(a: int, b: int) -> int:
            return a + b

        add(3, 4)
        # After the call, context is cleared
        assert _current_trace.get() is None

    def test_nested_spans_parent_child(self):
        trace_obj_ref: list = []

        @argus.trace(name="parent", kind="agent")
        def parent():
            return child()

        @argus.trace(name="child", kind="tool_call")
        def child():
            trace_obj_ref.append(_current_trace.get())
            return "done"

        parent()
        assert len(trace_obj_ref) == 1
        t = trace_obj_ref[0]
        assert len(t.spans) == 2  # parent span + child span

        parent_span = next(s for s in t.spans if s.name == "parent")
        child_span  = next(s for s in t.spans if s.name == "child")
        assert child_span.parent_span_id == parent_span.span_id

    def test_error_recorded_in_span(self):
        @argus.trace(name="failing", kind="internal")
        def fail():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            fail()

        # Context should be cleared even after error
        assert _current_trace.get() is None

    def test_context_restored_after_call(self):
        @argus.trace(name="isolated", kind="internal")
        def isolated():
            return 42

        isolated()
        assert _current_trace.get() is None
        assert _current_span.get() is None


# ---------------------------------------------------------------------------
# Trace decorator — async
# ---------------------------------------------------------------------------

class TestTraceDecoratorAsync:
    def setup_method(self):
        _current_trace.set(None)
        _current_span.set(None)

    def test_basic_async_trace(self):
        captured: list = []

        @argus.trace(name="async_func", kind="agent")
        async def async_func(x: int) -> int:
            captured.append(_current_trace.get())
            return x * 3

        result = asyncio.run(async_func(4))
        assert result == 12
        assert len(captured) == 1
        assert captured[0].spans[0].name == "async_func"

    def test_async_nested_spans(self):
        trace_ref: list = []

        @argus.trace(name="async_parent", kind="agent")
        async def async_parent():
            return await async_child()

        @argus.trace(name="async_child", kind="reason")
        async def async_child():
            trace_ref.append(_current_trace.get())
            return "ok"

        asyncio.run(async_parent())
        assert len(trace_ref) == 1
        t = trace_ref[0]
        assert len(t.spans) == 2

        parent_span = next(s for s in t.spans if s.name == "async_parent")
        child_span  = next(s for s in t.spans if s.name == "async_child")
        assert child_span.parent_span_id == parent_span.span_id


# ---------------------------------------------------------------------------
# Context manager usage
# ---------------------------------------------------------------------------

class TestTraceContextManager:
    def setup_method(self):
        _current_trace.set(None)
        _current_span.set(None)

    def test_context_manager_basic(self):
        with argus.trace("cm_span", kind="reason") as span:
            assert span is not None
            assert span.name == "cm_span"
            span.set_attribute("key", "value")

        assert _current_trace.get() is None

    def test_context_manager_span_finished(self):
        with argus.trace("timed_span", kind="internal") as span:
            pass  # Just enter and exit

        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.duration_ms >= 0


# ---------------------------------------------------------------------------
# Trace model — aggregation
# ---------------------------------------------------------------------------

class TestTraceAggregation:
    def test_finish_calculates_duration(self):
        t = argus.Trace(agent_name="test")
        t.finish()
        assert t.end_time is not None
        assert t.duration_ms is not None
        assert t.duration_ms >= 0

    def test_span_finish(self):
        t = argus.Trace(agent_name="test")
        s = argus.Span(trace_id=t.trace_id, name="s1", kind=SpanKind.INTERNAL)
        s.finish()
        assert s.duration_ms is not None

    def test_status_inherits_error_from_spans(self):
        t = argus.Trace(agent_name="test")
        s = argus.Span(trace_id=t.trace_id, name="bad", kind=SpanKind.TOOL_CALL)
        s.status = SpanStatus.ERROR
        s.error_message = "oops"
        t.spans.append(s)
        t.finish()
        assert t.status == SpanStatus.ERROR
        assert t.error_message == "oops"
