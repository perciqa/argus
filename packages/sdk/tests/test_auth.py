"""SDK auth tests — api_key propagation."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from argus.config import ArgusConfig, init, get_config
from argus.exporter import BatchExporter


def test_argus_config_defaults_api_key_to_empty():
    cfg = ArgusConfig()
    assert cfg.api_key == ""


def test_argus_config_api_key_explicit():
    cfg = ArgusConfig(api_key="sk-my-key")
    assert cfg.api_key == "sk-my-key"


def test_init_respects_api_key_param():
    init(server_url="http://example.com:8000", agent_name="test", api_key="sk-from-param")
    cfg = get_config()
    assert cfg.api_key == "sk-from-param"


def test_init_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("ARGUS_API_KEY", "sk-from-env")
    init(server_url="http://example.com:8000", agent_name="test")
    cfg = get_config()
    assert cfg.api_key == "sk-from-env"


def test_init_param_overrides_env(monkeypatch):
    monkeypatch.setenv("ARGUS_API_KEY", "sk-from-env")
    init(server_url="http://example.com:8000", agent_name="test", api_key="sk-from-param")
    cfg = get_config()
    assert cfg.api_key == "sk-from-param"


def test_exporter_stores_api_key():
    exporter = BatchExporter(api_key="sk-export-key")
    assert exporter.api_key == "sk-export-key"


def test_exporter_defaults_api_key_to_empty():
    exporter = BatchExporter()
    assert exporter.api_key == ""
