"""
Argus SDK — Batch exporter.

Collects completed traces and ships them to the Argus server
in async batches with retry logic and local fallback.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import httpx

if TYPE_CHECKING:
    from argus.models import Trace

logger = logging.getLogger("argus.exporter")


class BatchExporter:
    """
    Async batched trace exporter.

    Traces are enqueued (thread-safe) and flushed either when the batch
    reaches `batch_size` or when `flush_interval_seconds` elapses —
    whichever comes first.

    Falls back to writing JSON files locally if the server is unreachable.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        batch_size: int = 10,
        flush_interval_seconds: float = 5.0,
        fallback_dir: str = ".argus/traces",
        max_retries: int = 3,
        api_key: str = "",
    ):
        self.server_url            = server_url.rstrip("/")
        self.batch_size            = batch_size
        self.flush_interval        = flush_interval_seconds
        self.fallback_dir          = Path(fallback_dir)
        self.max_retries           = max_retries
        self.api_key               = api_key

        self._pending: list[Trace] = []
        self._lock                 = threading.Lock()
        self._client: Optional[httpx.AsyncClient] = None
        self._flush_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running              = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the exporter. Tries to attach to a running event loop;
        if none exists, launches one in a background thread.
        """
        try:
            loop = asyncio.get_running_loop()
            self._loop = loop
            self._client = httpx.AsyncClient(timeout=10.0)
            self._running = True
            self._flush_task = loop.create_task(self._flush_loop())
        except RuntimeError:
            # No running loop — start one in a daemon thread
            self._loop = asyncio.new_event_loop()
            t = threading.Thread(
                target=self._run_loop, daemon=True, name="argus-exporter"
            )
            t.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._async_start())

    async def _async_start(self) -> None:
        self._client  = httpx.AsyncClient(timeout=10.0)
        self._running = True
        await self._flush_loop()

    def stop(self) -> None:
        """Flush remaining traces and shut down."""
        self._running = False
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._flush_now(), self._loop).result(
                timeout=10
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(self, trace: "Trace") -> None:
        """Add a completed trace to the export queue. Thread-safe."""
        with self._lock:
            self._pending.append(trace)
            should_flush = len(self._pending) >= self.batch_size

        if should_flush and self._loop:
            if self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self._flush_now(), self._loop)

    # ------------------------------------------------------------------
    # Internal flush logic
    # ------------------------------------------------------------------

    async def _flush_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.flush_interval)
            await self._flush_now()

    async def _flush_now(self) -> None:
        with self._lock:
            if not self._pending:
                return
            batch, self._pending = self._pending[:], []

        for trace in batch:
            await self._send_with_retry(trace)

    async def _send_with_retry(self, trace: "Trace") -> None:
        url     = f"{self.server_url}/api/traces"
        payload = trace.model_dump(mode="json")
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                if self._client is None:
                    self._client = httpx.AsyncClient(timeout=10.0)
                resp = await self._client.post(url, json=payload, headers=headers)
                if resp.status_code < 300:
                    logger.debug("Exported trace %s", trace.trace_id)
                    return
                logger.warning(
                    "Server returned %s for trace %s (attempt %d/%d)",
                    resp.status_code, trace.trace_id, attempt + 1, self.max_retries,
                )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.debug(
                    "Export attempt %d failed for trace %s: %s",
                    attempt + 1, trace.trace_id, exc,
                )

            # Exponential backoff: 0.5s → 1s → 2s
            await asyncio.sleep(0.5 * (2 ** attempt))

        # All retries exhausted — write to disk
        self._write_fallback(trace)

    def _write_fallback(self, trace: "Trace") -> None:
        """Write a trace to a local JSON file as last-resort fallback."""
        try:
            self.fallback_dir.mkdir(parents=True, exist_ok=True)
            path = self.fallback_dir / f"{trace.trace_id}.json"
            path.write_text(trace.model_dump_json(indent=2))
            logger.info("Wrote fallback trace to %s", path)
        except Exception as exc:
            logger.error("Failed to write fallback trace: %s", exc)
