"""
Database initialization and connection management.
"""

import os
import aiosqlite
from pathlib import Path

DB_PATH = os.getenv("ARGUS_DB_PATH", "data/argus.db")

CREATE_TRACES_TABLE = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id        TEXT PRIMARY KEY,
    agent_name      TEXT NOT NULL DEFAULT 'default',
    task            TEXT,
    status          TEXT NOT NULL DEFAULT 'ok'
                        CHECK (status IN ('ok', 'error', 'drift', 'timeout')),
    start_time      TEXT NOT NULL,
    end_time        TEXT,
    duration_ms     REAL,
    total_tokens    INTEGER NOT NULL DEFAULT 0,
    total_cost_usd  REAL NOT NULL DEFAULT 0.0,
    local_tokens    INTEGER NOT NULL DEFAULT 0,
    cloud_tokens    INTEGER NOT NULL DEFAULT 0,
    model_calls_count INTEGER NOT NULL DEFAULT 0,
    tool_calls_count  INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT,
    metadata_json   TEXT DEFAULT '{}',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_traces_agent_name ON traces(agent_name);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time);
CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at);
"""

CREATE_SPANS_TABLE = """
CREATE TABLE IF NOT EXISTS spans (
    span_id         TEXT PRIMARY KEY,
    trace_id        TEXT NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    parent_span_id  TEXT,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL DEFAULT 'internal'
                        CHECK (kind IN ('agent', 'reason', 'tool_call', 'model_call', 'guardrail', 'internal')),
    status          TEXT NOT NULL DEFAULT 'ok'
                        CHECK (status IN ('ok', 'error', 'drift', 'timeout')),
    start_time      TEXT NOT NULL,
    end_time        TEXT,
    duration_ms     REAL,
    input_json      TEXT,
    output_json     TEXT,
    attributes_json TEXT DEFAULT '{}',
    events_json     TEXT DEFAULT '[]',
    error_message   TEXT,
    error_type      TEXT,
    model_name      TEXT,
    model_provider  TEXT,
    model_base_url  TEXT,
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    model_cost_usd  REAL,
    model_latency_ms REAL,
    model_cached    INTEGER DEFAULT 0,
    tool_name       TEXT,
    tool_args_json  TEXT,
    tool_result_json TEXT,
    tool_error      TEXT,
    tool_latency_ms REAL
);
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent ON spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_kind ON spans(kind);
"""

CREATE_EVAL_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS eval_results (
    eval_id         TEXT PRIMARY KEY,
    trace_id        TEXT NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    span_id         TEXT,
    overall_score   REAL NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    verdict         TEXT NOT NULL DEFAULT 'pass'
                        CHECK (verdict IN ('pass', 'fail', 'warn')),
    accuracy_score  REAL,
    reasoning_score REAL,
    tool_usage_score REAL,
    safety_score    REAL,
    judge_model     TEXT NOT NULL DEFAULT 'gemma',
    explanation     TEXT NOT NULL DEFAULT '',
    eval_latency_ms REAL,
    eval_cost_usd   REAL NOT NULL DEFAULT 0.0,
    evaluated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_evals_trace_id ON eval_results(trace_id);
CREATE INDEX IF NOT EXISTS idx_evals_verdict ON eval_results(verdict);
CREATE INDEX IF NOT EXISTS idx_evals_evaluated_at ON eval_results(evaluated_at);
"""

CREATE_COST_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS cost_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    period          TEXT NOT NULL,
    agent_name      TEXT NOT NULL DEFAULT 'default',
    total_cost_usd  REAL NOT NULL DEFAULT 0.0,
    local_cost_usd  REAL NOT NULL DEFAULT 0.0,
    cloud_cost_usd  REAL NOT NULL DEFAULT 0.0,
    total_tokens    INTEGER NOT NULL DEFAULT 0,
    local_tokens    INTEGER NOT NULL DEFAULT 0,
    cloud_tokens    INTEGER NOT NULL DEFAULT 0,
    trace_count     INTEGER NOT NULL DEFAULT 0,
    success_count   INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    UNIQUE(period, agent_name)
);
CREATE INDEX IF NOT EXISTS idx_cost_period ON cost_records(period);
CREATE INDEX IF NOT EXISTS idx_cost_agent ON cost_records(agent_name);
"""


async def init_db() -> None:
    """Create all tables and configure SQLite for concurrent access."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA busy_timeout=5000")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(CREATE_TRACES_TABLE)
        await db.executescript(CREATE_SPANS_TABLE)
        await db.executescript(CREATE_EVAL_RESULTS_TABLE)
        await db.executescript(CREATE_COST_RECORDS_TABLE)
        await db.commit()


def get_db_path() -> str:
    return DB_PATH
