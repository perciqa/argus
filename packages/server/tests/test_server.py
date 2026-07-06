"""Server integration tests."""

from __future__ import annotations

import asyncio
import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

# Use a named temp file so all aiosqlite connections share the same DB
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["ARGUS_DB_PATH"] = _tmp.name

from app.main import app  # noqa: E402
from app.db.database import init_db  # noqa: E402


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Traces — ingest + retrieve
# ---------------------------------------------------------------------------

SAMPLE_TRACE = {
    "trace_id":          "test-trace-001",
    "agent_name":        "test-agent",
    "task":              "Summarize the document",
    "status":            "ok",
    "start_time":        "2026-07-06T10:00:00.000Z",
    "end_time":          "2026-07-06T10:00:05.000Z",
    "duration_ms":       5000.0,
    "total_tokens":      1200,
    "total_cost_usd":    0.0,
    "local_tokens":      1200,
    "cloud_tokens":      0,
    "model_calls_count": 1,
    "tool_calls_count":  0,
    "spans": [
        {
            "span_id":    "span-001",
            "trace_id":   "test-trace-001",
            "name":       "test-agent",
            "kind":       "agent",
            "status":     "ok",
            "start_time": "2026-07-06T10:00:00.000Z",
            "end_time":   "2026-07-06T10:00:05.000Z",
            "duration_ms": 5000.0,
        },
        {
            "span_id":        "span-002",
            "trace_id":       "test-trace-001",
            "parent_span_id": "span-001",
            "name":           "gemma2:9b",
            "kind":           "model_call",
            "status":         "ok",
            "start_time":     "2026-07-06T10:00:01.000Z",
            "end_time":       "2026-07-06T10:00:04.000Z",
            "duration_ms":    3000.0,
            "model_call": {
                "model":             "gemma2:9b",
                "provider":          "local",
                "base_url":          "http://localhost:11434",
                "prompt_tokens":     800,
                "completion_tokens": 400,
                "total_tokens":      1200,
                "cost_usd":          0.0,
                "latency_ms":        3000.0,
            },
        },
    ],
}


@pytest.mark.asyncio
async def test_ingest_trace(client: AsyncClient):
    resp = await client.post("/api/traces", json=SAMPLE_TRACE)
    assert resp.status_code == 201
    data = resp.json()
    assert data["trace_id"] == "test-trace-001"
    assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_list_traces(client: AsyncClient):
    resp = await client.get("/api/traces")
    assert resp.status_code == 200
    data = resp.json()
    assert "traces" in data
    assert data["total"] >= 1
    trace = next((t for t in data["traces"] if t["trace_id"] == "test-trace-001"), None)
    assert trace is not None
    assert trace["agent_name"] == "test-agent"
    assert trace["total_cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_get_trace_detail(client: AsyncClient):
    resp = await client.get("/api/traces/test-trace-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace_id"] == "test-trace-001"
    assert len(data["spans"]) == 2

    model_span = next(s for s in data["spans"] if s["kind"] == "model_call")
    assert model_span["model_provider"] == "local"
    assert model_span["model_cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_get_trace_not_found(client: AsyncClient):
    resp = await client.get("/api/traces/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_traces_filter_by_agent(client: AsyncClient):
    resp = await client.get("/api/traces?agent_name=test-agent")
    assert resp.status_code == 200
    data = resp.json()
    for t in data["traces"]:
        assert t["agent_name"] == "test-agent"


# ---------------------------------------------------------------------------
# FinOps
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finops_summary(client: AsyncClient):
    resp = await client.get("/api/finops/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "today" in data
    assert "this_week" in data
    assert "all_time" in data
    # Local tokens always cost $0
    assert data["all_time"]["local_cost_usd"] == 0.0
    assert data["all_time"]["local_tokens"] >= 1200


@pytest.mark.asyncio
async def test_finops_timeseries(client: AsyncClient):
    resp = await client.get("/api/finops/timeseries?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_finops_breakdown(client: AsyncClient):
    resp = await client.get("/api/finops/breakdown")
    assert resp.status_code == 200
    data = resp.json()
    assert "by_agent" in data
    assert "by_model" in data


# ---------------------------------------------------------------------------
# Evals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_evals_empty(client: AsyncClient):
    resp = await client.get("/api/evals")
    assert resp.status_code == 200
    data = resp.json()
    assert "evals" in data
    assert "total" in data
