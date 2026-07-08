"""
Argus demo — simulated tools with full ratioc SDK instrumentation.

Each tool is wrapped with @argus.trace(kind="tool_call") so every invocation
appears as a discrete node in the trace tree with timing and I/O captured.
"""

import asyncio
import random

import ratioc as argus

_ORDERS = {
    "ORD-8821": {"order_id": "ORD-8821", "status": "delivered", "customer": "acme@example.com", "total_usd": 2450.00, "items": ["GPU Server Rack × 4", "Infiniband Switch × 2"]},
    "ORD-8822": {"order_id": "ORD-8822", "status": "pending",    "customer": "globex@example.com", "total_usd": 180.50, "items": ["Thermal Paste × 10"]},
    "ORD-8823": {"order_id": "ORD-8823", "status": "refunded",   "customer": "initech@example.com", "total_usd": 560.00, "items": ["NIC × 2", "DAC Cable × 4"]},
    "ORD-8824": {"order_id": "ORD-8824", "status": "shipped",    "customer": "umbrella@example.com", "total_usd": 12500.00, "items": ["AMD MI300X × 1"]},
}


@argus.trace(name="web_search", kind="tool_call")
async def search(query: str) -> dict:
    """
    Simulated web search returning static results for the demo.
    Captured as a tool_call span with I/O in the trace tree.
    """
    await asyncio.sleep(random.uniform(0.3, 0.8))

    snippets: list[dict] = []
    if "epyc" in query.lower() or "amd" in query.lower():
        snippets = [
            {"title": "AMD EPYC 9005 Series Benchmarks (June 2026)", "snippet": "The EPYC 9005 delivers 2.4× perf-per-watt over Intel Xeon 6900P in SPECrate2017_int_base, with 192 cores vs 120."},
            {"title": "Phoronix: EPYC 9965 vs Xeon 6980P — Linux Benchmarks", "snippet": "Across 65 real-world workloads, EPYC leads by 38% in geometric mean while consuming 22% less power."},
            {"title": "ServeTheHome: TCO Comparison — 1P EPYC 9005 vs 2P Xeon", "snippet": "Single-socket EPYC 9575F outperforms dual-socket Xeon 6780E at 60% lower platform cost."},
        ]
    elif "gpu" in query.lower() or "inference" in query.lower() or "local" in query.lower():
        snippets = [
            {"title": "Running Llama 3.1 70B Locally — 2026 Cost Analysis", "snippet": "AMD MI300X delivers 98 tok/s on Llama 3.1 70B Q4. Local inference saves $0.35 per 1M tokens vs Fireworks."},
            {"title": "Cloud vs On-Prem GPU Inference TCO (3-Year)", "snippet": "At 30% utilization, on-prem 4× MI300X breaks even in 8 months vs Fireworks serverless at the same throughput."},
        ]
    elif "tco" in query.lower() or "cost" in query.lower() or "budget" in query.lower():
        snippets = [
            {"title": "Agent Inference Economics (Q2 2026)", "snippet": "Hybrid routing saves 40-60% vs all-cloud: route simple tasks to local Gemma 3 27B ($0), complex to DeepSeek V4."},
            {"title": "Fireworks vs AMD Cloud — Real-World Agent Costs", "snippet": "Production data across 12 agents: avg $4.20/day cloud-only vs $1.37/day with hybrid local-routing."},
        ]
    else:
        snippets = [
            {"title": "Hybrid AI Infrastructure Benchmarks", "snippet": "Best practice in 2026: run classification and simple queries locally, reserve cloud for reasoning-heavy workloads."},
            {"title": "Agent Observability: Why Tracing Matters", "snippet": "Without per-model-call cost tracking, engineering teams underestimate cloud spend by 35-60%."},
        ]

    return {"query": query, "results": snippets, "total_results": len(snippets)}


@argus.trace(name="calculate", kind="tool_call")
async def calculate(expression: str) -> dict:
    """
    Safe arithmetic calculator.
    Captured as a tool_call span with the expression and result in I/O.
    """
    await asyncio.sleep(random.uniform(0.1, 0.3))

    try:
        result = eval(expression, {"__builtins__": {}}, {"int": int, "float": float, "abs": abs, "round": round, "pow": pow})
    except Exception:
        result = f"Error: could not evaluate '{expression}'"

    return {"expression": expression, "result": result}


@argus.trace(name="database_lookup", kind="tool_call")
async def lookup(key: str, database: str = "orders") -> dict:
    """
    Simulated database record lookup.
    Captured as a tool_call span with the lookup parameters and result.
    """
    await asyncio.sleep(random.uniform(0.2, 0.5))

    if database == "orders":
        record = _ORDERS.get(key, {"error": "not_found", "key": key})
    else:
        record = {"error": "unknown_database", "database": database}

    return {"database": database, "key": key, "record": record}
