"""
Argus demo agent — multi-model routing with full ratioc SDK instrumentation.

Demonstrates:
  - Hybrid local/cloud model routing (local=$0, cloud=priced)
  - Task classification → tool selection → model inference pipeline
  - Full trace tree with model_call + tool_call spans
  - FinOps cost tracking across the trace

Usage:
    python -m demo.agent          # interactive mode — enter tasks at prompt
    python -m demo.agent --demo   # run preset demo scenarios
"""

from __future__ import annotations

import asyncio
import os
import random
import time
import sys
from typing import Optional

import ratioc as argus
from ratioc.models import ModelCall, ModelProvider


SERVER_URL = os.environ.get("ARGUS_SERVER_URL", "http://localhost:8000")

argus.init(server_url=SERVER_URL, agent_name="multi-model-router", export_interval_seconds=2.0)


async def _local_llm(prompt: str) -> str:
    """
    Simulated call to a local model (Gemma 3 27B on AMD hardware — $0).
    Captured as a model_call span within the active trace.
    """
    with argus.trace("gemma3:27b", kind="model_call") as span:
        t0 = time.perf_counter()
        await asyncio.sleep(random.uniform(0.6, 1.4))
        elapsed = (time.perf_counter() - t0) * 1000

        prompt_tokens = min(600, max(80, len(prompt) // 3))
        completion_tokens = random.randint(60, 250)

        span.model_call = ModelCall(
            model="gemma3:27b",
            provider=ModelProvider.LOCAL,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=0.0,
            latency_ms=round(elapsed, 2),
            base_url="http://localhost:8080/v1",
        )

        output = f"[local/gemma3:27b response to: {prompt[:60]}...]"
        span.set_output(output)
        return output


async def _cloud_llm(prompt: str) -> str:
    """
    Simulated call to a cloud model (DeepSeek V4 Flash via Fireworks — priced).
    Captured as a model_call span within the active trace.
    """
    with argus.trace("deepseek-v4-flash", kind="model_call") as span:
        t0 = time.perf_counter()
        await asyncio.sleep(random.uniform(0.3, 0.8))
        elapsed = (time.perf_counter() - t0) * 1000

        prompt_tokens = min(900, max(100, len(prompt) // 2))
        completion_tokens = random.randint(100, 400)

        input_price  = prompt_tokens / 1_000_000 * 0.14
        output_price = completion_tokens / 1_000_000 * 0.28
        cost = round(input_price + output_price, 8)

        span.model_call = ModelCall(
            model="accounts/fireworks/models/deepseek-v4-flash",
            provider=ModelProvider.FIREWORKS,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            latency_ms=round(elapsed, 2),
            base_url="https://api.fireworks.ai/inference/v1",
        )

        output = f"[cloud/deepseek-v4-flash response to: {prompt[:60]}...]"
        span.set_output(output)
        return output


@argus.trace(name="classify_task", kind="reason")
async def classify_task(task: str) -> str:
    """
    Use a local model to classify the task type.
    Determines what tool to call and which model to use for the final answer.
    """
    prompt = f"Classify this task into one of: research, calculation, lookup, chat.\nTask: {task}"
    response = await _local_llm(prompt)

    task_lower = task.lower()
    if any(w in task_lower for w in ("calculate", "compute", "tco", "cost of", "how much", "total", "sum", "math")):
        return "calculation"
    elif any(w in task_lower for w in ("lookup", "order", "find", "check status", "retrieve", "show me")):
        return "lookup"
    elif any(w in task_lower for w in ("search", "benchmark", "compare", "latest", "research", "what is", "explain", "tell me about")):
        return "research"
    else:
        return "chat"


@argus.trace(name="execute_tool", kind="internal")
async def execute_tool(task_type: str, task: str) -> dict:
    """Route to the appropriate tool based on classified task type."""
    from demo.tools import search, calculate, lookup

    if task_type == "research":
        return await search(query=task)
    elif task_type == "calculation":
        expr = task.split(":")[-1].strip() if ":" in task else task
        return await calculate(expression=expr)
    elif task_type == "lookup":
        order_id = _extract_order_id(task) or task
        return await lookup(key=order_id, database="orders")
    else:
        return {"tool": "none", "reason": "chat — no tool needed"}


def _extract_order_id(task: str) -> Optional[str]:
    for word in task.split():
        if word.upper().startswith("ORD-"):
            return word.upper()
    return None


@argus.trace(name="generate_answer", kind="reason")
async def generate_answer(task_type: str, task: str, tool_result: dict) -> str:
    """
    Route the final answer generation to local or cloud depending on complexity.
    Local handles lookup + simple chat; cloud handles research + calculation.
    """
    prompt = f"Task: {task}\nTool result: {tool_result}\nGenerate a concise answer."

    if task_type in ("research", "calculation"):
        return await _cloud_llm(prompt)
    else:
        return await _local_llm(prompt)


@argus.trace(kind="agent")
async def run_agent(task: str) -> dict:
    """
    Full agent pipeline: classify → execute tool → generate answer.

    The @argus.trace(kind="agent") decorator creates a root trace that
    automatically aggregates token counts, costs, and status across all
    nested spans (model calls + tool calls + reasoning steps).
    """
    task_type = await classify_task(task)
    tool_result = await execute_tool(task_type, task)
    answer = await generate_answer(task_type, task, tool_result)

    return {
        "task": task,
        "task_type": task_type,
        "tool_result": tool_result,
        "answer": answer,
    }


# ---------------------------------------------------------------------------
# Demo scenarios
# ---------------------------------------------------------------------------

DEMO_SCENARIOS = [
    {
        "name": "Research: AMD EPYC vs Intel Xeon benchmarks",
        "task": "Search for the latest benchmarks comparing AMD EPYC 9005 to Intel Xeon 6900P and summarize the key findings",
    },
    {
        "name": "Calculation: TCO savings from hybrid routing",
        "task": "Calculate TCO: if cloud inference costs $4.20/day running 15,000 agents and local handles 40% of traffic at $0, what is the daily savings?",
    },
    {
        "name": "Lookup: customer order status",
        "task": "Look up the order status for ORD-8824",
    },
    {
        "name": "Lookup: missing order (error path)",
        "task": "Check order ORD-9999 status",
    },
    {
        "name": "Research: local vs cloud GPU costs",
        "task": "Compare the total cost of ownership for running LLM inference on local AMD MI300X GPUs versus Fireworks serverless cloud API over 3 years",
    },
]


async def run_demo() -> None:
    print("═" * 72)
    print("  Argus Demo Agent — Multi-Model Router")
    print(f"  Exporting traces to: {SERVER_URL}")
    print("═" * 72)

    for i, scenario in enumerate(DEMO_SCENARIOS, 1):
        print(f"\n▸ Scenario {i}/{len(DEMO_SCENARIOS)}: {scenario['name']}")
        print(f"  Task: {scenario['task']}")
        result = await run_agent(task=scenario["task"])
        print(f"  Type:   {result['task_type']}")
        print(f"  Answer: {result['answer'][:100]}...")
        await asyncio.sleep(1.0)

    print("\n═" * 72)
    print("  Demo complete. Traces exported to Argus.")
    print("  Open http://localhost:3000 to explore them.")
    print("═" * 72)


async def run_interactive() -> None:
    print("═" * 72)
    print("  Argus Demo Agent — Interactive Mode")
    print("  Type a task (or 'demo' to run scenarios, 'quit' to exit)")
    print("═" * 72)

    while True:
        try:
            task = input("\n▸ Task: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not task:
            continue
        if task.lower() == "quit":
            break
        if task.lower() == "demo":
            await run_demo()
            continue

        result = await run_agent(task=task)
        print(f"  Type:   {result['task_type']}")
        print(f"  Answer: {result['answer']}")


# ---------------------------------------------------------------------------
# Main (blocking wrapper for interactive use + SIGINT handling)
# ---------------------------------------------------------------------------

def main():
    if "--demo" in sys.argv:
        try:
            asyncio.run(run_demo())
        except KeyboardInterrupt:
            pass
        return

    try:
        asyncio.run(run_interactive())
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
