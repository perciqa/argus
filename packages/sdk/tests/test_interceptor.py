"""Interceptor unit tests — provider detection and trace integration."""

import pytest
from ratioc.interceptor import _detect_provider
from ratioc.models import ModelProvider, Trace, Span, SpanKind


class TestProviderDetection:
    def test_fireworks_url(self):
        assert _detect_provider("https://api.fireworks.ai/inference/v1") == ModelProvider.FIREWORKS

    def test_fireworks_host(self):
        assert _detect_provider("https://audio-fireworks.ai.example.com") == ModelProvider.FIREWORKS

    def test_openai_url(self):
        assert _detect_provider("https://api.openai.com/v1") == ModelProvider.OPENAI

    def test_anthropic_url(self):
        assert _detect_provider("https://api.anthropic.com/v1") == ModelProvider.ANTHROPIC

    def test_localhost(self):
        assert _detect_provider("http://localhost:11434/v1") == ModelProvider.LOCAL

    def test_loopback(self):
        assert _detect_provider("http://127.0.0.1:8080") == ModelProvider.LOCAL

    def test_amd_cloud(self):
        assert _detect_provider("http://amdcloud.internal/v1") == ModelProvider.LOCAL

    def test_rocm_host(self):
        assert _detect_provider("https://rocm-node.cluster/v1") == ModelProvider.LOCAL

    def test_unknown_provider(self):
        assert _detect_provider("https://some-random-api.example.com/v1") == ModelProvider.CUSTOM

    def test_empty_url(self):
        assert _detect_provider("") == ModelProvider.CUSTOM

    def test_url_case_insensitive(self):
        assert _detect_provider("https://API.FIREWORKS.AI/v1") == ModelProvider.FIREWORKS


class TestRecordModelCallIntegration:
    """Integration-style tests verifying _record_model_call works with active traces."""

    def test_record_with_active_trace_creates_model_span(self):
        from ratioc.interceptor import _record_model_call
        from ratioc.trace import _current_trace, _current_span

        trace = Trace(agent_name="test", trace_id="int-test-001")
        root = Span(
            span_id="root-span",
            trace_id="int-test-001",
            name="agent_root",
            kind=SpanKind.AGENT,
        )
        trace.spans.append(root)

        token_t = _current_trace.set(trace)
        token_s = _current_span.set(root)

        try:
            # Fake OpenAI-style response
            class FakeUsage:
                prompt_tokens = 320
                completion_tokens = 280
                total_tokens = 600

            class FakeChoice:
                class FakeMessage:
                    content = "Fake response text"
                message = FakeMessage()

            class FakeResponse:
                usage = FakeUsage()
                choices = [FakeChoice()]

            _record_model_call(
                base_url="http://localhost:11434/v1",
                model="gemma3:27b",
                messages=[{"role": "user", "content": "hello"}],
                response=FakeResponse(),
                elapsed_ms=450.0,
            )

            assert len(trace.spans) == 2
            model_span = trace.spans[1]
            assert model_span.kind == SpanKind.MODEL_CALL
            assert model_span.model_call.provider == ModelProvider.LOCAL
            assert model_span.model_call.prompt_tokens == 320
            assert model_span.model_call.completion_tokens == 280
            assert model_span.model_call.cost_usd == 0.0
            assert trace.model_calls_count == 1
            assert trace.local_tokens == 600
        finally:
            _current_trace.reset(token_t)
            _current_span.reset(token_s)

    def test_record_without_active_trace_is_noop(self):
        from ratioc.interceptor import _record_model_call
        from ratioc.trace import _current_trace, _current_span

        # Ensure no active trace
        _current_trace.set(None)
        _current_span.set(None)

        # Should not raise and should not create spans
        _record_model_call(
            base_url="https://api.fireworks.ai/inference/v1",
            model="deepseek-v4",
            messages=[],
            response=None,
            elapsed_ms=100.0,
        )

        assert _current_trace.get() is None

    def test_record_with_fireworks_provider_tracks_cloud_tokens(self):
        from ratioc.interceptor import _record_model_call
        from ratioc.trace import _current_trace, _current_span

        trace = Trace(agent_name="test", trace_id="fw-test-001")
        root = Span(span_id="r1", trace_id="fw-test-001", name="root", kind=SpanKind.AGENT)
        trace.spans.append(root)

        token_t = _current_trace.set(trace)
        token_s = _current_span.set(root)

        try:
            class FakeUsage:
                prompt_tokens = 500
                completion_tokens = 200
                total_tokens = 700

            class FakeChoice:
                class FakeMessage:
                    content = "cloud response"
                message = FakeMessage()

            class FakeResponse:
                usage = FakeUsage()
                choices = [FakeChoice()]

            _record_model_call(
                base_url="https://api.fireworks.ai/inference/v1",
                model="deepseek-v4-flash",
                messages=[{"role": "user", "content": "x"}],
                response=FakeResponse(),
                elapsed_ms=300.0,
            )

            assert trace.cloud_tokens == 700
            assert trace.local_tokens == 0
            provider = trace.spans[1].model_call.provider
            assert provider == ModelProvider.FIREWORKS
        finally:
            _current_trace.reset(token_t)
            _current_span.reset(token_s)

    def test_double_patch_is_idempotent(self):
        from ratioc.interceptor import patch_openai_client, _patched

        was_patched = _patched

        # Reset so we can test fresh
        import ratioc.interceptor as mod
        mod._patched = False

        try:
            patch_openai_client()
            first = mod._patched
            patch_openai_client()
            second = mod._patched
            assert first is True
            assert second is True
        finally:
            mod._patched = was_patched
