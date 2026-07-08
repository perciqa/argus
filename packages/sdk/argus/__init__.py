"""
Argus by Perciqa — Agent Reliability Engine SDK.

Quick start:
    import argus as argus

    argus.init(server_url="http://localhost:8000", agent_name="my-agent")

    @argus.trace(name="my_agent", kind="agent")
    def my_agent(query: str) -> str:
        result = search(query)
        return summarize(result)

    my_agent("Explain quantum entanglement")
"""

from argus.models import (
    Trace,
    Span,
    SpanKind,
    SpanStatus,
    ModelCall,
    ModelProvider,
    ToolCall,
    SpanEvent,
    EvalResult,
    EvalVerdict,
    CostRecord,
)
from argus.trace import (
    trace,
    start_trace,
    start_span,
    get_current_trace,
    get_current_span,
    BudgetExceededError,
)
from argus.config import init, get_config, get_exporter
from argus.cost import PRICING_TABLE, calculate_cost
from argus.interceptor import patch_openai_client

__version__ = "0.1.0"

__all__ = [
    # Decorator / context manager
    "trace",
    "start_trace",
    "start_span",
    "get_current_trace",
    "get_current_span",
    # Errors
    "BudgetExceededError",
    # Config
    "init",
    "get_config",
    "get_exporter",
    # Cost
    "PRICING_TABLE",
    "calculate_cost",
    # Interceptor
    "patch_openai_client",
    # Models
    "Trace",
    "Span",
    "SpanKind",
    "SpanStatus",
    "ModelCall",
    "ModelProvider",
    "ToolCall",
    "SpanEvent",
    "EvalResult",
    "EvalVerdict",
    "CostRecord",
]
