"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Badge, Card, Drawer, Group, Loader, Table, Text, Tooltip,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconAlertCircle, IconCheck, IconAlertTriangle } from "@tabler/icons-react";
import { listTraces, getTrace, type TraceSummary, type TraceDetail, type SpanRow } from "@/lib/api";
import { useArgusWebSocket } from "@/hooks/useArgusWebSocket";

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
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function fmtCost(usd: number) {
  if (usd === 0) return "$0.00";
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  return `$${usd.toFixed(4)}`;
}

function timeAgo(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60)   return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

const STATUS_PROPS: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  ok:      { color: "green",  icon: <IconCheck size={11} />,         label: "pass"    },
  error:   { color: "red",    icon: <IconAlertCircle size={11} />,   label: "fail"    },
  drift:   { color: "orange", icon: <IconAlertTriangle size={11} />, label: "drift"   },
  timeout: { color: "gray",   icon: <IconAlertCircle size={11} />,   label: "timeout" },
};

function StatusBadge({ status }: { status: string }) {
  const props = STATUS_PROPS[status] ?? STATUS_PROPS.ok;
  return (
    <Badge
      color={props.color}
      variant="light"
      size="sm"
      leftSection={props.icon}
    >
      {props.label}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Span tree
// ---------------------------------------------------------------------------

const KIND_CLASS: Record<string, string> = {
  agent:     "span-kind-agent",
  model_call:"span-kind-model",
  tool_call: "span-kind-tool",
  internal:  "span-kind-internal",
  guardrail: "span-kind-guardrail",
};

function SpanTree({ spans }: { spans: SpanRow[] }) {
  const sorted = [...spans].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  );

  // Build depth map for indentation
  const depthMap: Record<string, number> = {};
  sorted.forEach((s) => {
    depthMap[s.span_id] = s.parent_span_id
      ? (depthMap[s.parent_span_id] ?? 0) + 1
      : 0;
  });

  return (
    <div className="span-tree">
      {sorted.map((span) => {
        const depth = depthMap[span.span_id] ?? 0;
        const kindClass = KIND_CLASS[span.kind] ?? "span-kind-internal";
        return (
          <div key={span.span_id} className="span-row" style={{ paddingLeft: depth * 16 }}>
            <div className={`span-kind-indicator ${kindClass}`} />
            <div style={{ flex: 1 }}>
              <Text className="span-name" fw={500} size="sm">
                {span.name}
              </Text>
              <Text size="xs" c="dimmed" className="mono" mt={2}>
                {span.kind}
                {span.model_name && ` · ${span.model_name}`}
                {span.tool_name  && ` · ${span.tool_name}`}
                {span.duration_ms != null && ` · ${fmtMs(span.duration_ms)}`}
              </Text>
              {span.error_message && (
                <Text size="xs" c="red" mt={2}>{span.error_message}</Text>
              )}
            </div>
            <Text className="span-meta mono" size="xs" c="dimmed">
              {span.completion_tokens != null && `${span.completion_tokens} tok`}
              {span.model_cost_usd != null && span.model_cost_usd > 0 &&
                ` · ${fmtCost(span.model_cost_usd)}`}
            </Text>
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
  const [traces, setTraces]     = useState<TraceSummary[]>([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(true);
  const [selected, setSelected] = useState<TraceDetail | null>(null);
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
    useCallback((event: import("@/hooks/useArgusWebSocket").WsEvent) => {
      if (event.event === "new_trace") {
        const t = event.data as unknown as TraceSummary;
        newIds.current.add(t.trace_id);
        setTraces((prev) => [t, ...prev.slice(0, 49)]);
        setTotal((n) => n + 1);
        notifications.show({
          title: "New trace",
          message: `${t.agent_name}${t.task ? ` — ${t.task}` : ""}`,
          color: "blue",
          autoClose: 3000,
        });
        setTimeout(() => { newIds.current.delete(t.trace_id); }, 2000);
      }
      if (event.event === "eval_complete") {
        notifications.show({
          title: "Eval complete",
          message: `Score: ${(event.data as { overall_score?: number }).overall_score ?? "—"}`,
          color: "green",
          autoClose: 3000,
        });
      }
    }, [])
  );

  const openTrace = async (id: string) => {
    setDrawerOpen(true);
    setLoadingDetail(true);
    try {
      const detail = await getTrace(id);
      setSelected(detail);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Stat totals
  const todayCost   = traces.reduce((s, t) => s + t.total_cost_usd, 0);
  const localTokens = traces.reduce((s, t) => s + t.local_tokens, 0);
  const passRate    = traces.length
    ? Math.round((traces.filter((t) => t.status === "ok").length / traces.length) * 100)
    : 0;
  const agentNames  = new Set(traces.map((t) => t.agent_name)).size;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Traces</h1>
        <p className="page-subtitle">
          {total} total &nbsp;·&nbsp;
          <span
            style={{ display: "inline-flex", alignItems: "center", gap: 5 }}
          >
            <span
              className={`live-dot ${status === "connected" ? "connected" : "disconnected"}`}
            />
            <Text span size="xs" c="dimmed">
              {status === "connected" ? "Live" : "Reconnecting…"}
            </Text>
          </span>
        </p>
      </div>

      {/* Stat cards */}
      <div className="stat-cards-row">
        {[
          { label: "Cost Today",    value: fmtCost(todayCost),       mono: true  },
          { label: "Local Tokens",  value: fmtTokens(localTokens),   mono: true  },
          { label: "Pass Rate",     value: `${passRate}%`,           mono: false },
          { label: "Agents",        value: String(agentNames),       mono: false },
        ].map(({ label, value, mono }) => (
          <Card key={label} p="md">
            <Text className="stat-card-label">{label}</Text>
            <div className={`stat-card-value ${mono ? "mono" : ""}`}>{value}</div>
          </Card>
        ))}
      </div>

      {/* Traces table */}
      <Card p={0} style={{ overflow: "hidden" }}>
        <div style={{ padding: "14px 18px", borderBottom: "1px solid #e2e8f0" }}>
          <div className="section-title">
            Live Traces
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <Loader size="sm" color="blue" />
          </div>
        ) : traces.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center" }}>
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
                    cursor: "pointer",
                    background: newIds.current.has(t.trace_id)
                      ? "#eff6ff"
                      : undefined,
                    transition: "background 1s ease",
                  }}
                >
                  <Table.Td><StatusBadge status={t.status} /></Table.Td>
                  <Table.Td>
                    <Text size="sm" fw={500}>{t.agent_name}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Tooltip label={t.task ?? "—"} disabled={!t.task}>
                      <Text size="sm" c="dimmed" truncate maw={200}>
                        {t.task ?? <Text span c="dimmed" fs="italic">—</Text>}
                      </Text>
                    </Tooltip>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" className="mono">{fmtMs(t.duration_ms)}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" className="mono">{fmtTokens(t.total_tokens)}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" className="mono">{fmtCost(t.total_cost_usd)}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">{timeAgo(t.created_at)}</Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      {/* Span detail drawer */}
      <Drawer
        opened={drawerOpen}
        onClose={() => { setDrawerOpen(false); setSelected(null); }}
        title={
          <Group gap="xs">
            <Text fw={600} size="sm">Span timeline</Text>
            {selected && <StatusBadge status={selected.status} />}
          </Group>
        }
        position="right"
        size="lg"
        styles={{
          header: { borderBottom: "1px solid #e2e8f0", paddingBottom: 12 },
          body: { paddingTop: 16 },
        }}
      >
        {loadingDetail ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Loader size="sm" color="blue" />
          </div>
        ) : selected ? (
          <>
            {/* Trace meta */}
            <div style={{ marginBottom: 20, padding: "12px 0", borderBottom: "1px solid #f1f5f9" }}>
              <Group justify="space-between" mb={6}>
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Agent</Text>
                <Text size="sm" fw={500}>{selected.agent_name}</Text>
              </Group>
              {selected.task && (
                <Group justify="space-between" mb={6}>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Task</Text>
                  <Text size="sm">{selected.task}</Text>
                </Group>
              )}
              <Group justify="space-between" mb={6}>
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Duration</Text>
                <Text size="sm" className="mono">{fmtMs(selected.duration_ms)}</Text>
              </Group>
              <Group justify="space-between" mb={6}>
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Tokens</Text>
                <Text size="sm" className="mono">{selected.total_tokens.toLocaleString()}</Text>
              </Group>
              <Group justify="space-between">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>Cost</Text>
                <Text size="sm" className="mono" c={selected.total_cost_usd === 0 ? "green" : undefined}>
                  {fmtCost(selected.total_cost_usd)}
                  {selected.total_cost_usd === 0 && " (local)"}
                </Text>
              </Group>
            </div>

            {/* Spans */}
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={10}>
              Spans ({selected.spans.length})
            </Text>
            <SpanTree spans={selected.spans} />
          </>
        ) : null}
      </Drawer>
    </div>
  );
}
