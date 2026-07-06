"""
Argus Server — API request/response schemas.

These mirror the SDK's wire format (ratioc.models) without
importing the SDK package, keeping the server self-contained.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# Inbound (SDK wire format)
# ---------------------------------------------------------------------------

class SpanKindIn(str, Enum):
    AGENT      = "agent"
    REASON     = "reason"
    TOOL_CALL  = "tool_call"
    MODEL_CALL = "model_call"
    GUARDRAIL  = "guardrail"
    INTERNAL   = "internal"


class SpanStatusIn(str, Enum):
    OK      = "ok"
    ERROR   = "error"
    DRIFT   = "drift"
    TIMEOUT = "timeout"


class ModelProviderIn(str, Enum):
    OPENAI    = "openai"
    FIREWORKS = "fireworks"
    ANTHROPIC = "anthropic"
    LOCAL     = "local"
    CUSTOM    = "custom"


class ModelCallIn(BaseModel):
    model:             str
    provider:          ModelProviderIn = ModelProviderIn.LOCAL
    base_url:          str             = ""
    prompt_tokens:     int             = 0
    completion_tokens: int             = 0
    total_tokens:      int             = 0
    cost_usd:          float           = 0.0
    latency_ms:        Optional[float] = None
    cached:            bool            = False


class ToolCallIn(BaseModel):
    name:       str
    arguments:  Any          = None
    result:     Any          = None
    error:      Optional[str]= None
    latency_ms: Optional[float] = None


class SpanIn(BaseModel):
    span_id:        str
    trace_id:       str
    parent_span_id: Optional[str]   = None
    name:           str
    kind:           SpanKindIn      = SpanKindIn.INTERNAL
    status:         SpanStatusIn    = SpanStatusIn.OK
    start_time:     datetime
    end_time:       Optional[datetime] = None
    duration_ms:    Optional[float] = None
    input_data:     Any             = None
    output_data:    Any             = None
    attributes:     dict            = Field(default_factory=dict)
    events:         list            = Field(default_factory=list)
    error_message:  Optional[str]   = None
    error_type:     Optional[str]   = None
    model_call:     Optional[ModelCallIn] = None
    tool_call:      Optional[ToolCallIn]  = None


class TraceIn(BaseModel):
    trace_id:           str
    agent_name:         str             = "default"
    task:               Optional[str]   = None
    status:             SpanStatusIn    = SpanStatusIn.OK
    start_time:         datetime
    end_time:           Optional[datetime] = None
    duration_ms:        Optional[float] = None
    total_tokens:       int             = 0
    total_cost_usd:     float           = 0.0
    local_tokens:       int             = 0
    cloud_tokens:       int             = 0
    model_calls_count:  int             = 0
    tool_calls_count:   int             = 0
    error_message:      Optional[str]   = None
    metadata:           dict            = Field(default_factory=dict)
    spans:              list[SpanIn]    = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Outbound (API responses)
# ---------------------------------------------------------------------------

class TraceSummary(BaseModel):
    trace_id:           str
    agent_name:         str
    task:               Optional[str]
    status:             str
    start_time:         str
    end_time:           Optional[str]
    duration_ms:        Optional[float]
    total_tokens:       int
    total_cost_usd:     float
    local_tokens:       int
    cloud_tokens:       int
    model_calls_count:  int
    tool_calls_count:   int
    span_count:         int
    error_message:      Optional[str]
    created_at:         str


class TraceDetail(TraceSummary):
    spans: list[dict]


class TraceListResponse(BaseModel):
    traces: list[TraceSummary]
    total:  int
    limit:  int
    offset: int


class FinOpsPeriod(BaseModel):
    total_cost_usd:     float
    local_cost_usd:     float
    cloud_cost_usd:     float
    local_tokens:       int
    cloud_tokens:       int
    total_tokens:       int
    trace_count:        int
    avg_cost_per_trace: float
    savings_usd:        float  # vs running everything on cloud


class FinOpsSummary(BaseModel):
    today:      FinOpsPeriod
    this_week:  FinOpsPeriod
    all_time:   FinOpsPeriod


class TimeseriesPoint(BaseModel):
    date:           str
    total_cost_usd: float
    local_tokens:   int
    cloud_tokens:   int
    trace_count:    int


class EvalSummary(BaseModel):
    eval_id:        str
    trace_id:       str
    overall_score:  float
    verdict:        str
    judge_model:    str
    explanation:    str
    evaluated_at:   str
    agent_name:     Optional[str] = None


class EvalListResponse(BaseModel):
    evals:           list[EvalSummary]
    total:           int
    avg_score:       Optional[float]
    pass_rate:       Optional[float]
