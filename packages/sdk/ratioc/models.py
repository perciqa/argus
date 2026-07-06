"""
Ratioc data models — Pydantic v2 schemas for traces, spans, model calls, and eval results.

These models define the wire format between the SDK and the Ratioc server,
and are designed to be OpenTelemetry-compatible in structure.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SpanKind(str, Enum):
    """Type of span in an agent trajectory."""
    AGENT = "agent"
    REASON = "reason"
    TOOL_CALL = "tool_call"
    MODEL_CALL = "model_call"
    GUARDRAIL = "guardrail"
    INTERNAL = "internal"


class SpanStatus(str, Enum):
    """Outcome status of a span."""
    OK = "ok"
    ERROR = "error"
    DRIFT = "drift"       # Agent deviated from expected behavior
    TIMEOUT = "timeout"


class ModelProvider(str, Enum):
    """Where the model inference ran."""
    LOCAL = "local"        # Local GPU (AMD Developer Cloud / ROCm) — $0 cost
    FIREWORKS = "fireworks"  # Fireworks AI API
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class EvalVerdict(str, Enum):
    """Outcome of an LLM-as-judge evaluation."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

def _generate_id() -> str:
    """Generate a compact hex ID."""
    return uuid.uuid4().hex[:16]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ModelCall(BaseModel):
    """A single LLM inference call captured by the interceptor."""
    model: str = Field(..., description="Model identifier (e.g. 'accounts/fireworks/models/gemma-27b')")
    provider: ModelProvider = Field(default=ModelProvider.CUSTOM)
    base_url: Optional[str] = Field(default=None, description="API base URL used for the call")
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0, description="Estimated cost in USD")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Call latency in milliseconds")
    cached: bool = Field(default=False, description="Whether the response was served from cache")

    def model_post_init(self, __context: Any) -> None:
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class ToolCall(BaseModel):
    """A tool/function call made by an agent."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = Field(default=0.0, ge=0.0)


class SpanEvent(BaseModel):
    """A discrete event within a span (e.g., validation started, guardrail triggered)."""
    name: str
    timestamp: datetime = Field(default_factory=_now)
    attributes: dict[str, Any] = Field(default_factory=dict)


class Span(BaseModel):
    """
    A single unit of work in an agent trajectory.

    Spans form a tree: each span can have a parent_span_id pointing to its parent.
    The root span has parent_span_id = None.
    """
    span_id: str = Field(default_factory=_generate_id)
    trace_id: str = Field(..., description="ID of the parent trace")
    parent_span_id: Optional[str] = Field(default=None)
    name: str = Field(..., description="Human-readable name (e.g., 'search_flights')")
    kind: SpanKind = Field(default=SpanKind.INTERNAL)
    status: SpanStatus = Field(default=SpanStatus.OK)

    # Timing
    start_time: datetime = Field(default_factory=_now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Content
    input_data: Optional[Any] = Field(default=None, description="Input to this span")
    output_data: Optional[Any] = Field(default=None, description="Output from this span")
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[SpanEvent] = Field(default_factory=list)

    # Linked sub-objects
    model_call: Optional[ModelCall] = None
    tool_call: Optional[ToolCall] = None

    # Error info
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    def finish(self) -> None:
        """Mark this span as complete and calculate duration."""
        self.end_time = _now()
        delta = self.end_time - self.start_time
        self.duration_ms = delta.total_seconds() * 1000

    def add_event(self, name: str, **attributes: Any) -> None:
        """Record a discrete event within this span."""
        self.events.append(SpanEvent(name=name, attributes=attributes))


class Trace(BaseModel):
    """
    A complete agent trajectory — the top-level container for a tree of spans.

    A trace represents one end-to-end agent task execution.
    """
    trace_id: str = Field(default_factory=_generate_id)
    agent_name: str = Field(default="default", description="Name of the agent that produced this trace")
    task: Optional[str] = Field(default=None, description="Human-readable task description")

    # Timing
    start_time: datetime = Field(default_factory=_now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Spans
    spans: list[Span] = Field(default_factory=list)

    # Aggregated metrics
    total_tokens: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    local_tokens: int = Field(default=0, ge=0, description="Tokens processed locally ($0)")
    cloud_tokens: int = Field(default=0, ge=0, description="Tokens processed via cloud API")
    model_calls_count: int = Field(default=0, ge=0)
    tool_calls_count: int = Field(default=0, ge=0)

    # Status
    status: SpanStatus = Field(default=SpanStatus.OK)
    error_message: Optional[str] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def finish(self) -> None:
        """Finalize the trace: set end time, aggregate metrics from spans."""
        self.end_time = _now()
        delta = self.end_time - self.start_time
        self.duration_ms = delta.total_seconds() * 1000
        self._aggregate_metrics()

    def _aggregate_metrics(self) -> None:
        """Roll up token counts, costs, and call counts from all spans."""
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        self.local_tokens = 0
        self.cloud_tokens = 0
        self.model_calls_count = 0
        self.tool_calls_count = 0

        for span in self.spans:
            if span.model_call:
                mc = span.model_call
                self.total_tokens += mc.total_tokens
                self.total_cost_usd += mc.cost_usd
                self.model_calls_count += 1
                if mc.provider == ModelProvider.LOCAL:
                    self.local_tokens += mc.total_tokens
                else:
                    self.cloud_tokens += mc.total_tokens
            if span.tool_call:
                self.tool_calls_count += 1

        # Inherit worst status from spans
        for span in self.spans:
            if span.status == SpanStatus.ERROR:
                self.status = SpanStatus.ERROR
                self.error_message = span.error_message
                break
            elif span.status == SpanStatus.DRIFT:
                self.status = SpanStatus.DRIFT


class EvalResult(BaseModel):
    """Result of an LLM-as-judge evaluation on a trace or span."""
    eval_id: str = Field(default_factory=_generate_id)
    trace_id: str
    span_id: Optional[str] = Field(default=None, description="If evaluating a specific span")

    # Scores
    overall_score: float = Field(..., ge=0.0, le=100.0)
    verdict: EvalVerdict = Field(default=EvalVerdict.PASS)

    # Breakdown
    accuracy_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    reasoning_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    tool_usage_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    safety_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)

    # Judge details
    judge_model: str = Field(default="gemma", description="Model used as judge")
    explanation: str = Field(default="", description="Judge's reasoning")

    # Meta
    evaluated_at: datetime = Field(default_factory=_now)
    eval_latency_ms: Optional[float] = None
    eval_cost_usd: float = Field(default=0.0, ge=0.0)


class CostRecord(BaseModel):
    """Aggregated cost record for FinOps dashboards."""
    period: str = Field(..., description="Time period (e.g., '2026-07-06T14:00')")
    agent_name: str = Field(default="default")
    total_cost_usd: float = Field(default=0.0)
    local_cost_usd: float = Field(default=0.0)
    cloud_cost_usd: float = Field(default=0.0)
    total_tokens: int = Field(default=0)
    local_tokens: int = Field(default=0)
    cloud_tokens: int = Field(default=0)
    trace_count: int = Field(default=0)
    success_count: int = Field(default=0)
    error_count: int = Field(default=0)
