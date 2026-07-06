"""
Argus SDK — Cost calculator.

Pricing table and cost calculation for model inference calls.
Local inference (AMD Developer Cloud / ROCm) is always $0.00.
"""

from __future__ import annotations

from ratioc.models import ModelProvider

# ---------------------------------------------------------------------------
# Per 1M tokens pricing table
# ---------------------------------------------------------------------------

PRICING_TABLE: dict[str, dict[str, float]] = {
    # Local models — always free (AMD Developer Cloud / ROCm)
    "local": {"input": 0.00, "output": 0.00},

    # Fireworks AI models (July 2026)
    "accounts/fireworks/models/gemma2-9b-it":              {"input": 0.05,  "output": 0.05},
    "accounts/fireworks/models/gemma-27b-it":              {"input": 0.10,  "output": 0.10},
    "accounts/fireworks/models/deepseek-v3":               {"input": 0.90,  "output": 0.90},
    "accounts/fireworks/models/deepseek-r1":               {"input": 3.00,  "output": 8.00},
    "accounts/fireworks/models/qwen3-30b-a3b":             {"input": 0.15,  "output": 0.60},
    "accounts/fireworks/models/qwen3-235b-a22b":           {"input": 0.22,  "output": 0.88},
    "accounts/fireworks/models/llama-v3p1-8b-instruct":    {"input": 0.05,  "output": 0.05},
    "accounts/fireworks/models/llama-v3p1-70b-instruct":   {"input": 0.35,  "output": 0.40},
    "accounts/fireworks/models/llama-v3p1-405b-instruct":  {"input": 0.80,  "output": 0.80},
    "accounts/fireworks/models/mixtral-8x7b-instruct":     {"input": 0.20,  "output": 0.20},

    # OpenAI models
    "gpt-4o":           {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":      {"input": 0.15,  "output": 0.60},
    "gpt-4-turbo":      {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo":    {"input": 0.50,  "output": 1.50},

    # Anthropic models
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307":    {"input": 0.25, "output": 1.25},

    # Fallback for unknown models
    "default": {"input": 1.00, "output": 2.00},
}


def calculate_cost(
    model: str,
    provider: ModelProvider,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """
    Calculate the estimated cost of a model call in USD.

    Local providers (AMD GPU, localhost) always return $0.00
    regardless of token count — this is the core FinOps value prop.
    """
    if provider == ModelProvider.LOCAL:
        return 0.0

    pricing = PRICING_TABLE.get(model) or PRICING_TABLE["default"]
    input_cost  = (prompt_tokens    / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 8)
