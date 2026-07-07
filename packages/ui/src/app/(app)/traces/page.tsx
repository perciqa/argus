"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Badge, Drawer, Group, Loader, Table, Text, Tooltip } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  IconCheck, IconAlertCircle, IconAlertTriangle,
  IconTimeline, IconCoin, IconBolt, IconShieldCheck, IconUsers,
} from "@tabler/icons-react";
import { listTraces, getTrace, type TraceSummary, type TraceDetail, type SpanRow } from "@/lib/api";
import { useArgusWebSocket } from "@/hooks/useArgusWebSocket";
import type { WsEvent } from "@/hooks/useArgusWebSocket";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtMs(ms: number | null) {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function fmtTokens(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function fmtCost(usd: number) {
  if (usd === 0) return "$0.00";
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  return `$${usd.toFixed(4)}`;
}

function timeAgo(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

const STATUS_META: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  ok:      { color: "green",  icon: <IconCheck size={11} />,         label: "pass"    },
  error:   { color: "red",    icon: <IconAlertCircle size={11} />,   label: "fail"    },
  drift:   { color: "orange", icon: <IconAlertTriangle size={11} />, label: "drift"   },
  timeout: { color: "gray",   icon: <IconAlertCircle size={11} />,   label: "timeout" },
};

function StatusBadge({ status }: { status: string }) {
  const m = STATUS_META[status] ?? STATUS_META.ok;
  return (
    <Badge color={m.color} variant="light" size="sm" radius="sm" leftSection={m.icon}>
      {m.label}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Gantt-style span timeline
// ---------------------------------------------------------------------------

function SpanTimeline({ spans }: { spans: SpanRow[] }) {
  const sorted = [...spans].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  );

  // Build depth map
  const depthMap: Record<string, number> = {};
  sorted.forEach((s) => {
    depthMap[s.span_id] = s.parent_span_id ? (depthMap[s.parent_span_id] ?? 0) + 1 : 0;
  });

  // Find max duration for bar width scaling
  const maxMs = Math.max(...sorted.map((s) => s.duration_ms ?? 0), 1);

  const KIND_CSS_CLASS: Record<string, string> = {
    agent:      "agent",
    model_call: "model_call",
    tool_call:  "tool_call",
    internal:   "internal",
    guardrail:  "guardrail",
  };

  return (
    <div className="span-timeline">
      {sorted.map((span) => {
        const depth = depthMap[span.span_id] ?? 0;
        const cls   = KIND_CSS_CLASS[span.kind] ?? "internal";
        const pct   = Math.max(4, ((span.duration_ms ?? 0) / maxMs) * 100);

        return (
          <div
            key={span.span_id}
            className="span-timeline-row"
            style={{ paddingLeft: depth * 14 }}
          >
            {/* Name row */}
            <div className="span-timeline-header">
              <div className={`span-kind-dot ${cls}`} />
              <span className="span-timeline-name">{span.name}</span>
              <span className="span-timeline-duration">{fmtMs(span.duration_ms)}</span>
            </div>

            {/* Duration bar */}
            <div className="span-duration-bar-wrap">
              <div
                className={`span-duration-bar ${cls}`}
                style={{ width: `${pct}%` }}
              />
            </div>

            {/* Meta row */}
            <div className="span-timeline-meta">
              <span>{span.kind.replace("_", " ")}</span>
              {span.model_name && <span>{span.model_name}</span>}
              {span.tool_name  && <span>{span.tool_name}</span>}
              {span.completion_tokens != null && <span>{span.completion_tokens} tok</span>}
              {span.model_cost_usd != null && span.model_cost_usd > 0 && (
                <span>{fmtCost(span.model_cost_usd)}</span>
              )}
              {span.error_message && (
                <span style={{ color: "var(--color-error)" }}>{span.error_message}</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function TracesPage() {
  const [traces, setTraces]         = useState<TraceSummary[]>([]);
  const [total, setTotal]           = useState(0);
  const [loading, setLoading]       = useState(true);
  const [selected, setSelected]     = useState<TraceDetail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const newIds = useRef<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      const data = await listTraces({ limit: 50 });
      setTraces(data.traces);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const { status } = useArgusWebSocket(
    useCallback((event: WsEvent) => {
      if (event.event === "new_trace") {
        const t = event.data as unknown as TraceSummary;
        newIds.current.add(t.trace_id);
        setTraces((prev) => [t, ...prev.slice(0, 49)]);
        setTotal((n) => n + 1);
        notifications.show({
          title: "New trace",
          message: `${t.agent_name}${t.task ? ` · ${t.task}` : ""}`,
          color: "blue",
          autoClose: 3000,
        });
        setTimeout(() => { newIds.current.delete(t.trace_id); }, 2000);
      }
      if (event.event === "eval_complete") {
        const d = event.data as { overall_score?: number; verdict?: string };
        notifications.show({
          title: "Eval complete",
          message: `Score ${d.overall_score?.toFixed(1) ?? "—"} · ${d.verdict ?? ""}`,
          color: "teal",
          autoClose: 4000,
        });
      }
    }, [])
  );

  const openTrace = async (id: string) => {
    setDrawerOpen(true);
    setLoadingDetail(true);
    try {
      setSelected(await getTrace(id));
    } finally {
      setLoadingDetail(false);
    }
  };

  // Stats
  const todayCost   = traces.reduce((s, t) => s + t.total_cost_usd, 0);
  const localTokens = traces.reduce((s, t) => s + t.local_tokens, 0);
  const passRate    = traces.length
    ? Math.round((traces.filter((t) => t.status === "ok").length / traces.length) * 100)
    : 0;
  const agentCount  = new Set(traces.map((t) => t.agent_name)).size;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Traces</h1>
          <p className="page-subtitle">{total} total</p>
        </div>
        <span className={`live-badge ${status === "connected" ? "connected" : "disconnected"}`}>
          <span className="live-dot" />
          {status === "connected" ? "Live" : "Reconnecting…"}
        </span>
      </div>

      {/* KPI cards */}
      <div className="stat-cards-row">
        <div className="stat-card">
          <div className="stat-card-icon blue"><IconCoin size={16} stroke={1.8} /></div>
          <div className="stat-card-label">Cost Today</div>
          <div className="stat-card-value mono">{fmtCost(todayCost)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon green"><IconBolt size={16} stroke={1.8} /></div>
          <div className="stat-card-label">Local Tokens</div>
          <div className="stat-card-value mono">{fmtTokens(localTokens)}</div>
          <div className="stat-card-delta">$0.00 (free)</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon violet"><IconShieldCheck size={16} stroke={1.8} /></div>
          <div className="stat-card-label">Pass Rate</div>
          <div className="stat-card-value">{passRate}%</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-icon amber"><IconUsers size={16} stroke={1.8} /></div>
          <div className="stat-card-label">Agents</div>
          <div className="stat-card-value">{agentCount}</div>
        </div>
      </div>

      {/* Traces table */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-header-title">
            <IconTimeline size={14} />
            Live Traces
          </span>
        </div>

        {loading ? (
          <div style={{ padding: 48, display: "flex", justifyContent: "center" }}>
            <Loader size="sm" color="blue" />
          </div>
        ) : traces.length === 0 ? (
          <div style={{ padding: "40px 18px", textAlign: "center" }}>
            <Text size="sm" c="dimmed">No traces yet. Instrument your agent with the Argus SDK.</Text>
          </div>
        ) : (
          <Table className="trace-table" horizontalSpacing="md" verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Status</Table.Th>
                <Table.Th>Agent</Table.Th>
                <Table.Th>Task</Table.Th>
                <Table.Th>Duration</Table.Th>
                <Table.Th>Tokens</Table.Th>
                <Table.Th>Cost</Table.Th>
                <Table.Th>Time</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {traces.map((t) => (
                <Table.Tr
                  key={t.trace_id}
                  onClick={() => openTrace(t.trace_id)}
                  style={{
                    background: newIds.current.has(t.trace_id) ? "var(--color-accent-bg)" : undefined,
                    transition: "background 1.5s ease",
                  }}
                >
                  <Table.Td><StatusBadge status={t.status} /></Table.Td>
                  <Table.Td><Text size="sm" fw={500}>{t.agent_name}</Text></Table.Td>
                  <Table.Td>
                    <Tooltip label={t.task ?? "—"} disabled={!t.task} withArrow>
                      <Text size="sm" c="dimmed" style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {t.task ?? "—"}
                      </Text>
                    </Tooltip>
                  </Table.Td>
                  <Table.Td><Text size="sm" className="mono">{fmtMs(t.duration_ms)}</Text></Table.Td>
                  <Table.Td><Text size="sm" className="mono">{fmtTokens(t.total_tokens)}</Text></Table.Td>
                  <Table.Td><Text size="sm" className="mono">{fmtCost(t.total_cost_usd)}</Text></Table.Td>
                  <Table.Td><Text size="sm" c="dimmed">{timeAgo(t.created_at)}</Text></Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </div>

      {/* Span timeline drawer */}
      <Drawer
        opened={drawerOpen}
        onClose={() => { setDrawerOpen(false); setSelected(null); }}
        title={
          <Group gap="xs">
            <Text fw={700} size="sm">Span timeline</Text>
            {selected && <StatusBadge status={selected.status} />}
          </Group>
        }
        position="right"
        size="lg"
        styles={{
          header: { borderBottom: "1px solid var(--color-border)", paddingBottom: 12 },
          body:   { paddingTop: 16, paddingLeft: 20, paddingRight: 20 },
        }}
      >
        {loadingDetail ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
            <Loader size="sm" color="blue" />
          </div>
        ) : selected ? (
          <>
            {/* Trace meta */}
            <div style={{ marginBottom: 20 }}>
              {[
                { label: "Agent",    value: selected.agent_name },
                { label: "Task",     value: selected.task ?? "—" },
                { label: "Duration", value: fmtMs(selected.duration_ms), mono: true },
                { label: "Tokens",   value: selected.total_tokens.toLocaleString(), mono: true },
                { label: "Cost",     value: fmtCost(selected.total_cost_usd) + (selected.total_cost_usd === 0 ? " (local)" : ""), mono: true, green: selected.total_cost_usd === 0 },
              ].map(({ label, value, mono, green }) => (
                <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--color-border-subtle)" }}>
                  <Text size="xs" tt="uppercase" fw={600} c="dimmed" style={{ letterSpacing: "0.05em" }}>{label}</Text>
                  <Text size="sm" fw={500} className={mono ? "mono" : ""} c={green ? "green" : undefined}>{value}</Text>
                </div>
              ))}
            </div>

            <Text size="xs" tt="uppercase" fw={600} c="dimmed" mb={10} style={{ letterSpacing: "0.05em" }}>
              Spans ({selected.spans.length})
            </Text>

            {/* Legend */}
            <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
              {[
                { cls: "agent",      label: "Agent" },
                { cls: "model_call", label: "Model" },
                { cls: "tool_call",  label: "Tool"  },
                { cls: "internal",   label: "Internal" },
              ].map(({ cls, label }) => (
                <div key={cls} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "var(--color-text-secondary)" }}>
                  <div className={`span-kind-dot ${cls}`} />
                  {label}
                </div>
              ))}
            </div>

            <SpanTimeline spans={selected.spans} />
          </>
        ) : null}
      </Drawer>
    </div>
  );
}
