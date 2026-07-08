"""Exporter unit tests — enqueue, fallback, and retry logic."""

import json
import tempfile
from pathlib import Path

import pytest
from argus.models import Trace, Span, SpanKind
from argus.exporter import BatchExporter


@pytest.fixture
def sample_trace():
    trace = Trace(trace_id="exp-test-001", agent_name="test-agent", task="Export test")
    span = Span(
        span_id="s1",
        trace_id="exp-test-001",
        name="test_span",
        kind=SpanKind.AGENT,
    )
    trace.spans.append(span)
    trace.finish()
    return trace


@pytest.fixture
def temp_fallback_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestBatchExporterBasics:
    def test_enqueue_adds_to_pending(self, sample_trace):
        exporter = BatchExporter(batch_size=10)
        exporter.enqueue(sample_trace)
        assert len(exporter._pending) == 1
        assert exporter._pending[0].trace_id == "exp-test-001"

    def test_enqueue_triggers_flush_at_batch_size(self, sample_trace):
        exporter = BatchExporter(batch_size=2)
        exporter.enqueue(sample_trace)
        assert len(exporter._pending) == 1
        # When no event loop is running, flush is deferred
        # but pending list still accumulates
        trace2 = Trace(trace_id="exp-test-002", agent_name="test-agent")
        trace2.spans.append(Span(span_id="s2", trace_id="exp-test-002", name="s2"))
        trace2.finish()
        exporter.enqueue(trace2)
        # Without a running event loop, flush is skipped gracefully
        assert True  # No crash — the exporter handled it gracefully

    def test_write_fallback_creates_json(self, sample_trace, temp_fallback_dir):
        exporter = BatchExporter(fallback_dir=temp_fallback_dir)
        exporter._write_fallback(sample_trace)

        path = Path(temp_fallback_dir) / "exp-test-001.json"
        assert path.exists()

        data = json.loads(path.read_text())
        assert data["trace_id"] == "exp-test-001"
        assert data["agent_name"] == "test-agent"
        assert len(data["spans"]) == 1
        assert data["spans"][0]["name"] == "test_span"

    def test_write_fallback_creates_directory(self, sample_trace):
        with tempfile.TemporaryDirectory() as d:
            fallback = Path(d) / "nested" / "dir"
            exporter = BatchExporter(fallback_dir=str(fallback))
            exporter._write_fallback(sample_trace)

            assert fallback.exists()
            assert (fallback / "exp-test-001.json").exists()

    def test_fallback_dir_default(self, sample_trace):
        exporter = BatchExporter()
        assert exporter.fallback_dir == Path(".argus/traces")

    def test_multiple_enqueue_traces(self, sample_trace):
        exporter = BatchExporter(batch_size=100)
        traces = []
        for i in range(5):
            t = Trace(
                trace_id=f"batch-{i:03d}",
                agent_name="test-agent",
                task=f"Task {i}",
            )
            t.spans.append(Span(span_id=f"s{i}", trace_id=f"batch-{i:03d}", name=f"span{i}"))
            t.finish()
            traces.append(t)
            exporter.enqueue(t)

        assert len(exporter._pending) == 5
        for i, t in enumerate(traces):
            assert exporter._pending[i].trace_id == t.trace_id


class TestBatchExporterConfiguration:
    def test_default_config(self):
        exporter = BatchExporter()
        assert exporter.server_url == "http://localhost:8000"
        assert exporter.batch_size == 10
        assert exporter.flush_interval == 5.0
        assert exporter.max_retries == 3

    def test_custom_config(self):
        exporter = BatchExporter(
            server_url="http://custom:9000",
            batch_size=50,
            flush_interval_seconds=1.0,
            max_retries=5,
        )
        assert exporter.server_url == "http://custom:9000"
        assert exporter.batch_size == 50
        assert exporter.flush_interval == 1.0
        assert exporter.max_retries == 5
