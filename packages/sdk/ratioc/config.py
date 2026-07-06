"""
Argus SDK — SDK configuration and init().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ArgusConfig:
    """Resolved runtime configuration for the Argus SDK."""
    server_url:              str            = "http://localhost:8000"
    agent_name:              str            = "default"
    budget_cap_usd:          Optional[float] = None
    export_batch_size:       int            = 10
    export_interval_seconds: float          = 5.0
    fallback_dir:            str            = ".argus/traces"
    auto_intercept:          bool           = True
    custom_pricing:          dict           = field(default_factory=dict)


# Module-level singletons — set by init()
_config:   Optional[ArgusConfig]  = None
_exporter: Optional[object]       = None   # BatchExporter, typed loosely to avoid circular import


def get_config() -> ArgusConfig:
    """Return the current config, initializing with defaults if needed."""
    global _config
    if _config is None:
        _config = ArgusConfig()
    return _config


def get_exporter():
    """Return the active exporter, creating a default one if needed."""
    global _exporter
    if _exporter is None:
        from ratioc.exporter import BatchExporter
        cfg = get_config()
        _exporter = BatchExporter(
            server_url=cfg.server_url,
            batch_size=cfg.export_batch_size,
            flush_interval_seconds=cfg.export_interval_seconds,
            fallback_dir=cfg.fallback_dir,
        )
        _exporter.start()
    return _exporter


def init(
    server_url:              str            = "http://localhost:8000",
    agent_name:              str            = "default",
    budget_cap_usd:          Optional[float] = None,
    export_batch_size:       int            = 10,
    export_interval_seconds: float          = 5.0,
    fallback_dir:            str            = ".argus/traces",
    auto_intercept:          bool           = True,
    custom_pricing:          Optional[dict]  = None,
) -> None:
    """
    Initialize the Argus SDK.

    Call this once at application startup. If not called, the SDK
    uses sensible defaults (localhost:8000, auto-intercept enabled).

    Args:
        server_url:              URL of the Argus server.
        agent_name:              Name tag for all traces from this process.
        budget_cap_usd:          Kill a trace if total cost exceeds this value.
        export_batch_size:       Number of traces to batch before flushing.
        export_interval_seconds: Max seconds between flushes.
        fallback_dir:            Directory for fallback JSON traces.
        auto_intercept:          Whether to auto-patch the OpenAI client.
        custom_pricing:          Override or extend the default pricing table.
    """
    global _config, _exporter

    _config = ArgusConfig(
        server_url=server_url,
        agent_name=agent_name,
        budget_cap_usd=budget_cap_usd,
        export_batch_size=export_batch_size,
        export_interval_seconds=export_interval_seconds,
        fallback_dir=fallback_dir,
        auto_intercept=auto_intercept,
        custom_pricing=custom_pricing or {},
    )

    # Apply custom pricing
    if custom_pricing:
        from ratioc.cost import PRICING_TABLE
        PRICING_TABLE.update(custom_pricing)

    # Start exporter
    from ratioc.exporter import BatchExporter
    _exporter = BatchExporter(
        server_url=server_url,
        batch_size=export_batch_size,
        flush_interval_seconds=export_interval_seconds,
        fallback_dir=fallback_dir,
    )
    _exporter.start()

    # Auto-patch OpenAI client
    if auto_intercept:
        from ratioc.interceptor import patch_openai_client
        patch_openai_client()
