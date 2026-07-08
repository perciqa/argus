"""
Argus Server — Database repository.

All SQLite read/write operations live here.
Routes stay thin; they call repository functions and return HTTP responses.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import aiosqlite

from app.db.database import DB_PATH

logger = logging.getLogger("argus.repository")


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


# ---------------------------------------------------------------------------
# Trace writes
# ---------------------------------------------------------------------------

async def upsert_trace(trace: dict) -> None:
    """Persist a complete trace (header + all spans) to SQLite."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        await db.execute("""
            INSERT OR REPLACE INTO traces (
                trace_id, agent_name, task, status,
                start_time, end_time, duration_ms,
                total_tokens, total_cost_usd, local_tokens, cloud_tokens,
                model_calls_count, tool_calls_count,
                error_message, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE(
                    (SELECT created_at FROM traces WHERE trace_id = ?),
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            )
        """, (
            trace["trace_id"],
            trace.get("agent_name", "default"),
            trace.get("task"),
            trace.get("status", "ok"),
            trace["start_time"],
            trace.get("end_time"),
            trace.get("duration_ms"),
            trace.get("total_tokens", 0),
            trace.get("total_cost_usd", 0.0),
            trace.get("local_tokens", 0),
            trace.get("cloud_tokens", 0),
            trace.get("model_calls_count", 0),
            trace.get("tool_calls_count", 0),
            trace.get("error_message"),
            json.dumps(trace.get("metadata", {})),
            trace["trace_id"],  # for COALESCE lookup
        ))

        for span in trace.get("spans", []):
            mc = span.get("model_call") or {}
            tc = span.get("tool_call") or {}
            await db.execute("""
                INSERT OR REPLACE INTO spans (
                    span_id, trace_id, parent_span_id, name, kind, status,
                    start_time, end_time, duration_ms,
                    input_json, output_json, attributes_json, events_json,
                    error_message, error_type,
                    model_name, model_provider, model_base_url,
                    prompt_tokens, completion_tokens,
                    model_cost_usd, model_latency_ms, model_cached,
                    tool_name, tool_args_json, tool_result_json,
                    tool_error, tool_latency_ms
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
            """, (
                span["span_id"],
                span["trace_id"],
                span.get("parent_span_id"),
                span["name"],
                span.get("kind", "internal"),
                span.get("status", "ok"),
                span["start_time"],
                span.get("end_time"),
                span.get("duration_ms"),
                _json(span.get("input_data")),
                _json(span.get("output_data")),
                _json(span.get("attributes", {})),
                _json(span.get("events", [])),
                span.get("error_message"),
                span.get("error_type"),
                mc.get("model"),
                mc.get("provider"),
                mc.get("base_url"),
                mc.get("prompt_tokens"),
                mc.get("completion_tokens"),
                mc.get("cost_usd"),
                mc.get("latency_ms"),
                1 if mc.get("cached") else 0,
                tc.get("name"),
                _json(tc.get("arguments")),
                _json(tc.get("result")),
                tc.get("error"),
                tc.get("latency_ms"),
            ))

        await db.commit()

        # Materialize cost record for FinOps dashboards
        await _materialize_cost_record(db, trace)


async def _materialize_cost_record(db: aiosqlite.Connection, trace: dict) -> None:
    """Upsert an hourly cost bucket from a newly ingested trace."""
    hour = trace.get("start_time", "")[:13] + ":00"
    agent = trace.get("agent_name", "default")
    cost  = trace.get("total_cost_usd", 0.0)
    tokens = trace.get("total_tokens", 0)
    local_t = trace.get("local_tokens", 0)
    cloud_t = trace.get("cloud_tokens", 0)
    is_success = 1 if trace.get("status") == "ok" else 0
    is_error   = 1 if trace.get("status") == "error" else 0

    await db.execute("""
        INSERT INTO cost_records
            (period, agent_name, total_cost_usd, local_cost_usd, cloud_cost_usd,
             total_tokens, local_tokens, cloud_tokens,
             trace_count, success_count, error_count)
        VALUES (?, ?, ?, 0.0, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(period, agent_name) DO UPDATE SET
            total_cost_usd = total_cost_usd + excluded.total_cost_usd,
            cloud_cost_usd = cloud_cost_usd + excluded.cloud_cost_usd,
            total_tokens   = total_tokens   + excluded.total_tokens,
            local_tokens   = local_tokens   + excluded.local_tokens,
            cloud_tokens   = cloud_tokens   + excluded.cloud_tokens,
            trace_count    = trace_count    + 1,
            success_count  = success_count  + excluded.success_count,
            error_count    = error_count    + excluded.error_count
    """, (hour, agent, cost, cost, tokens, local_t, cloud_t, is_success, is_error))
    await db.commit()


# ---------------------------------------------------------------------------
# Trace reads
# ---------------------------------------------------------------------------

async def list_traces(
    limit: int = 50,
    offset: int = 0,
    agent_name: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[list[dict], int]:
    """Return (rows, total_count) for the traces list endpoint."""
    where, params = _build_trace_filter(agent_name, status)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        count_row = await db.execute_fetchall(
            f"SELECT COUNT(*) as n FROM traces {where}", params
        )
        total = count_row[0]["n"] if count_row else 0

        rows = await db.execute_fetchall(f"""
            SELECT
                t.*,
                (SELECT COUNT(*) FROM spans s WHERE s.trace_id = t.trace_id) AS span_count
            FROM traces t
            {where}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
        """, [*params, limit, offset])

        return [dict(r) for r in rows], total


async def get_trace_detail(trace_id: str) -> Optional[dict]:
    """Return trace header + all spans, or None if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        rows = await db.execute_fetchall(
            "SELECT * FROM traces WHERE trace_id = ?", [trace_id]
        )
        if not rows:
            return None
        trace = dict(rows[0])

        span_rows = await db.execute_fetchall(
            "SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time", [trace_id]
        )
        trace["spans"] = [_deserialize_span(dict(s)) for s in span_rows]
        trace["span_count"] = len(trace["spans"])
        return trace


# ---------------------------------------------------------------------------
# FinOps reads
# ---------------------------------------------------------------------------

async def get_finops_summary() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        today     = await _finops_period(db, "DATE(created_at) = DATE('now')")
        this_week = await _finops_period(db, "DATE(created_at) >= DATE('now', '-6 days')")
        all_time  = await _finops_period(db, "1=1")
        return {"today": today, "this_week": this_week, "all_time": all_time}


async def get_finops_timeseries(days: int = 7) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(f"""
            SELECT
                DATE(created_at)      AS date,
                SUM(total_cost_usd)   AS total_cost_usd,
                SUM(local_tokens)     AS local_tokens,
                SUM(cloud_tokens)     AS cloud_tokens,
                COUNT(*)              AS trace_count
            FROM traces
            WHERE DATE(created_at) >= DATE('now', '-{days - 1} days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        return [dict(r) for r in rows]


async def get_finops_breakdown() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        by_agent = await db.execute_fetchall("""
            SELECT agent_name,
                   COUNT(*)            AS trace_count,
                   SUM(total_cost_usd) AS total_cost_usd,
                   SUM(local_tokens)   AS local_tokens,
                   SUM(cloud_tokens)   AS cloud_tokens
            FROM traces
            GROUP BY agent_name
            ORDER BY total_cost_usd DESC
        """)

        by_model = await db.execute_fetchall("""
            SELECT model_name,
                   model_provider,
                   COUNT(*)             AS call_count,
                   SUM(prompt_tokens)   AS prompt_tokens,
                   SUM(completion_tokens) AS completion_tokens,
                   SUM(model_cost_usd)  AS total_cost_usd
            FROM spans
            WHERE model_name IS NOT NULL
            GROUP BY model_name, model_provider
            ORDER BY total_cost_usd DESC
        """)

        return {
            "by_agent": [dict(r) for r in by_agent],
            "by_model": [dict(r) for r in by_model],
        }


# ---------------------------------------------------------------------------
# Eval reads
# ---------------------------------------------------------------------------

async def list_evals(limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        count_row = await db.execute_fetchall(
            "SELECT COUNT(*) as n FROM eval_results"
        )
        total = count_row[0]["n"] if count_row else 0

        rows = await db.execute_fetchall("""
            SELECT e.*, t.agent_name
            FROM eval_results e
            LEFT JOIN traces t ON t.trace_id = e.trace_id
            ORDER BY e.evaluated_at DESC
            LIMIT ? OFFSET ?
        """, [limit, offset])

        return [dict(r) for r in rows], total


async def get_eval_scores(days: int = 7) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(f"""
            SELECT
                DATE(evaluated_at)       AS date,
                AVG(overall_score)       AS avg_score,
                COUNT(*)                 AS eval_count,
                SUM(CASE WHEN verdict='pass' THEN 1 ELSE 0 END) AS pass_count
            FROM eval_results
            WHERE DATE(evaluated_at) >= DATE('now', '-{days - 1} days')
            GROUP BY DATE(evaluated_at)
            ORDER BY date
        """)
        return [dict(r) for r in rows]


async def upsert_eval(eval_data: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO eval_results (
                eval_id, trace_id, span_id, overall_score, verdict,
                accuracy_score, reasoning_score, tool_usage_score, safety_score,
                judge_model, explanation, eval_latency_ms, eval_cost_usd, evaluated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE(
                    (SELECT evaluated_at FROM eval_results WHERE eval_id = ?),
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                )
            )
        """, (
            eval_data["eval_id"], eval_data["trace_id"], eval_data.get("span_id"),
            eval_data["overall_score"], eval_data["verdict"],
            eval_data.get("accuracy_score"), eval_data.get("reasoning_score"),
            eval_data.get("tool_usage_score"), eval_data.get("safety_score"),
            eval_data.get("judge_model", "gemma"),
            eval_data.get("explanation", ""),
            eval_data.get("eval_latency_ms"), eval_data.get("eval_cost_usd", 0.0),
            eval_data["eval_id"],
        ))
        await db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


def _build_trace_filter(
    agent_name: Optional[str],
    status: Optional[str],
) -> tuple[str, list]:
    clauses, params = [], []
    if agent_name:
        clauses.append("agent_name = ?")
        params.append(agent_name)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def _deserialize_span(row: dict) -> dict:
    """Parse JSON columns back into dicts for span detail responses."""
    for col in ("input_json", "output_json", "attributes_json", "events_json",
                "tool_args_json", "tool_result_json"):
        if row.get(col):
            try:
                row[col] = json.loads(row[col])
            except Exception:
                pass
    return row


async def _finops_period(db: aiosqlite.Connection, where: str) -> dict:
    rows = await db.execute_fetchall(f"""
        SELECT
            COALESCE(SUM(total_cost_usd), 0)  AS total_cost_usd,
            COALESCE(SUM(local_tokens), 0)    AS local_tokens,
            COALESCE(SUM(cloud_tokens), 0)    AS cloud_tokens,
            COALESCE(SUM(total_tokens), 0)    AS total_tokens,
            COUNT(*)                          AS trace_count
        FROM traces
        WHERE {where}
    """)
    r = dict(rows[0]) if rows else {}
    total_cost   = r.get("total_cost_usd", 0.0)
    trace_count  = r.get("trace_count", 0)
    local_tokens = r.get("local_tokens", 0)
    cloud_tokens = r.get("cloud_tokens", 0)

    # Savings = what local tokens would have cost at the cheapest cloud rate ($0.05/1M)
    savings = (local_tokens / 1_000_000) * 0.05

    return {
        "total_cost_usd":     round(total_cost, 6),
        "local_cost_usd":     0.0,
        "cloud_cost_usd":     round(total_cost, 6),
        "local_tokens":       local_tokens,
        "cloud_tokens":       cloud_tokens,
        "total_tokens":       r.get("total_tokens", 0),
        "trace_count":        trace_count,
        "avg_cost_per_trace": round(total_cost / trace_count, 6) if trace_count else 0.0,
        "savings_usd":        round(savings, 6),
    }
