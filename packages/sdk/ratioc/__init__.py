"""
Argus SDK — The Agent Reliability Engine.

Quick start:
    import argus

    @argus.trace(name="my_agent", kind="agent")
    def my_agent(query: str) -> str:
        ...

    argus.init(server_url="http://localhost:8000", agent_name="my-agent")
"""

from ratioc.models import (
    Trace,
    Span,
    SpanKind,
    SpanStatus,
    ModelCall,
    ModelProvider,
    ToolCall,
    EvalResult,
    EvalVerdict,
    CostRecord,
)

# These will be filled in on Day 1
# from argus.trace import trace, start_trace, start_span
# from argus.interceptor import patch_openai_client
# from argus.exporter import BatchExporter
# from argus.cost import PRICING_TABLE, calculate_cost
# from argus.config import init

__version__ = "0.1.0"
__all__ = [
    "Trace",
    "Span",
    "SpanKind",
    "SpanStatus",
    "ModelCall",
    "ModelProvider",
    "ToolCall",
    "EvalResult",
    "EvalVerdict",
    "CostRecord",
]
