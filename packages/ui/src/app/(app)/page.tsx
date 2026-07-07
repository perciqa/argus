"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Card, Grid, Group, Loader, RingProgress, Text } from "@mantine/core";
import { AreaChart } from "@mantine/charts";
import {
  IconTimeline, IconCoins, IconChartBar,
  IconArrowRight, IconCheck, IconAlertCircle, IconAlertTriangle,
  IconTrendingUp, IconCoin, IconBolt, IconShieldCheck,
} from "@tabler/icons-react";
import {
  getFinOpsSummary, getTimeseries, listTraces, listEvals,
  type TraceSummary, type FinOpsSummary, type TimeseriesPoint, type EvalListResponse,
} from "@/lib/api";
import { useArgusWebSocket } from "@/hooks/useArgusWebSocket";
import type { WsEvent } from "@/hooks/useArgusWebSocket";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtCost(usd: number) {
  if (usd === 0) return "$0.00";
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(2)}`;
}

function fmtTokens(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function timeAgo(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  ok:      <IconCheck size={12} />,
  error:   <IconAlertCircle size={12} />,
  drift:   <IconAlertTriangle size={12} />,
  timeout: <IconAlertCircle size={12} />,
};

const STATUS_COLOR: Record<string, string> = {
  ok: "green", error: "red", drift: "orange", timeout: "gray",
};

// ---------------------------------------------------------------------------
// Health bar
// ---------------------------------------------------------------------------

function HealthBar({ traces }: { traces: TraceSummary[] }) {
  if (traces.length === 0) return null;
  const passCount = traces.filter((t) => t.status === "ok").length;
  const passRate  = Math.round((passCount / traces.length) * 100);
  const isHealthy = passRate >= 90;
  const isWarn    = passRate >= 70;

  const bg    = isHealthy ? "#f0fdf4" : isWarn ? "#fffbeb" : "#fef2f2";
  const color = isHealthy ? "#059669"  : isWarn ? "#d97706"  : "#dc2626";
  const label = isHealthy ? "All systems healthy" : isWarn ? "Some agents need attention" : "Agents degraded";

  return (
    <div style={{
      background: bg,
      border: `1px solid ${isHealthy ? "#a7f3d0" : isWarn ? "#fde68a" : "#fecaca"}`,
      borderRadius: 10,
      padding: "12px 18px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 20,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }} />
        <Text size="sm" fw={600} c={color}>{label}</Text>
        <Text size="sm" c="dimmed">·</Text>
        <Text size="sm" c="dimmed">{passCount} of {traces.length} traces passing</Text>
      </div>
      <Text size="sm" fw={700} style={{ fontFamily: "var(--font-mono)", color }}>{passRate}%</Text>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function OverviewPage() {
  const [traces, setTraces]   = useState<TraceSummary[]>([]);
  const [finops, setFinops]   = useState<FinOpsSummary | null>(null);
  const [series, setSeries]   = useState<TimeseriesPoint[]>([]);
  const [evals, setEvals]     = useState<EvalListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      listTraces({ limit: 8 }),
      getFinOpsSummary(),
      getTimeseries(7),
      listEvals(20),
    ]).then(([t, f, s, e]) => {
      setTraces(t.traces);
      setFinops(f);
      setSeries(s);
      setEvals(e);
    }).finally(() => setLoading(false));
  }, []);

  const { status } = useArgusWebSocket(
    useCallback((event: WsEvent) => {
      if (event.event === "new_trace") {
        const t = event.data as unknown as TraceSummary;
        setTraces((prev) => [t, ...prev.slice(0, 7)]);
      }
    }, [])
  );

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <Loader color="blue" size="sm" />
      </div>
    );
  }

  const today    = finops?.today;
  const allTime  = finops?.all_time;
  const passRate = evals?.pass_rate ?? null;
  const avgScore = evals?.avg_score ?? null;

  // Unique agents
  const agentNames = new Set(traces.map((t) => t.agent_name)).size;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Overview</h1>
        <p className="page-subtitle">
          Real-time agent monitoring &amp; reliability · {" "}
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <span className={`live-badge ${status === "connected" ? "connected" : "disconnected"}`}>
              <span className="live-dot" />
              {status === "connected" ? "Live" : "Reconnecting…"}
            </span>
          </span>
        </p>
      </div>

      {/* Health bar */}
      <HealthBar traces={traces} />

      {/* KPI cards */}
      <div className="stat-cards-row" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
        {/* Cost today */}
        <div className="stat-card">
          <div className="stat-card-icon blue">
            <IconCoin size={16} stroke={1.8} />
          </div>
          <div className="stat-card-label">Cost Today</div>
          <div className="stat-card-value mono">{fmtCost(today?.total_cost_usd ?? 0)}</div>
          {(allTime?.savings_usd ?? 0) > 0 && (
            <div className="stat-card-delta up">
              ↓ {fmtCost(allTime!.savings_usd)} saved all time
            </div>
          )}
        </div>

        {/* Local tokens */}
        <div className="stat-card">
          <div className="stat-card-icon green">
            <IconBolt size={16} stroke={1.8} />
          </div>
          <div className="stat-card-label">Local Tokens</div>
          <div className="stat-card-value mono">{fmtTokens(today?.local_tokens ?? 0)}</div>
          <div className="stat-card-delta">$0.00 · AMD hardware</div>
        </div>

        {/* Pass rate */}
        <div className="stat-card">
          <div className="stat-card-icon violet">
            <IconShieldCheck size={16} stroke={1.8} />
          </div>
          <div className="stat-card-label">Pass Rate</div>
          <div className="stat-card-value">
            {passRate != null ? `${(passRate * 100).toFixed(0)}%` : `${traces.filter(t=>t.status==="ok").length}/${traces.length}`}
          </div>
          {avgScore != null && (
            <div className="stat-card-delta">avg score {avgScore.toFixed(1)}</div>
          )}
        </div>

        {/* Agents */}
        <div className="stat-card">
          <div className="stat-card-icon amber">
            <IconTrendingUp size={16} stroke={1.8} />
          </div>
          <div className="stat-card-label">Active Agents</div>
          <div className="stat-card-value">{agentNames}</div>
          <div className="stat-card-delta">{today?.trace_count ?? traces.length} traces today</div>
        </div>
      </div>

      {/* Cost chart + Score ring */}
      <Grid mb={16}>
        <Grid.Col span={8}>
          <div className="panel">
            <div className="panel-header">
              <span className="panel-header-title">
                <IconCoins size={14} />
                Daily Cost — 7 days
              </span>
            </div>
            <div className="panel-body">
              {series.length === 0 ? (
                <Text size="sm" c="dimmed" ta="center" py={32}>No data yet — send some traces to see costs</Text>
              ) : (
                <AreaChart
                  h={180}
                  data={series}
                  dataKey="date"
                  series={[{ name: "total_cost_usd", label: "Cost ($)", color: "blue" }]}
                  curveType="monotone"
                  withLegend={false}
                  withDots={series.length < 10}
                  gridAxis="y"
                  tickLine="none"
                  valueFormatter={(v) => fmtCost(v as number)}
                  styles={{ root: { fontSize: 11 } }}
                />
              )}
            </div>
          </div>
        </Grid.Col>

        <Grid.Col span={4}>
          <div className="panel" style={{ height: "100%" }}>
            <div className="panel-header">
              <span className="panel-header-title">
                <IconChartBar size={14} />
                Eval Health
              </span>
            </div>
            <div className="panel-body" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingTop: 8 }}>
              {evals && (evals.total ?? 0) > 0 ? (
                <>
                  <RingProgress
                    size={120}
                    thickness={10}
                    roundCaps
                    sections={[
                      { value: (passRate ?? 0) * 100, color: "green" },
                      { value: (1 - (passRate ?? 0)) * 100, color: "#e2e8f0" },
                    ]}
                    label={
                      <Text ta="center" fw={700} size="lg" c="green">
                        {passRate != null ? `${((passRate) * 100).toFixed(0)}%` : "—"}
                      </Text>
                    }
                  />
                  <Text size="xs" c="dimmed" ta="center" mt={4}>Pass rate · {evals.total} evals</Text>
                  {avgScore != null && (
                    <Text size="xs" c="dimmed" ta="center">Avg score: {avgScore.toFixed(1)}/100</Text>
                  )}
                </>
              ) : (
                <Text size="sm" c="dimmed" ta="center">No evals yet</Text>
              )}
            </div>
          </div>
        </Grid.Col>
      </Grid>

      {/* Recent traces + Quick links */}
      <Grid>
        <Grid.Col span={8}>
          <div className="panel">
            <div className="panel-header">
              <span className="panel-header-title">
                <IconTimeline size={14} />
                Recent Traces
              </span>
              <Link href="/traces" style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--color-accent)", textDecoration: "none", fontWeight: 500 }}>
                View all <IconArrowRight size={12} />
              </Link>
            </div>
            {traces.length === 0 ? (
              <div className="panel-body">
                <Text size="sm" c="dimmed" ta="center" py={24}>
                  No traces yet. Instrument your agent with the Argus SDK.
                </Text>
              </div>
            ) : (
              <div>
                {traces.map((t) => (
                  <Link key={t.trace_id} href="/traces" style={{ textDecoration: "none" }}>
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: "10px 18px",
                      borderBottom: "1px solid var(--color-border-subtle)",
                      cursor: "pointer",
                      transition: "background 0.1s",
                    }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-page)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "")}
                    >
                      <Badge
                        size="xs"
                        radius="sm"
                        color={STATUS_COLOR[t.status] ?? "gray"}
                        variant="light"
                        leftSection={STATUS_ICON[t.status]}
                      >
                        {t.status === "ok" ? "pass" : t.status}
                      </Badge>
                      <Text size="sm" fw={500} style={{ flex: 1, minWidth: 0 }}>{t.agent_name}</Text>
                      <Text size="xs" c="dimmed" style={{ flex: 2, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {t.task ?? "—"}
                      </Text>
                      <Text size="xs" c="dimmed" className="mono" style={{ flexShrink: 0 }}>
                        {fmtCost(t.total_cost_usd)}
                      </Text>
                      <Text size="xs" c="dimmed" style={{ flexShrink: 0, minWidth: 50, textAlign: "right" }}>
                        {timeAgo(t.created_at)}
                      </Text>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </Grid.Col>

        {/* Quick navigation cards */}
        <Grid.Col span={4}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              {
                href: "/traces",
                icon: <IconTimeline size={18} stroke={1.6} />,
                label: "Traces",
                sub: "Live agent execution logs",
                color: "var(--color-accent)",
                bg: "var(--color-accent-bg)",
              },
              {
                href: "/finops",
                icon: <IconCoins size={18} stroke={1.6} />,
                label: "FinOps",
                sub: "Cost & savings breakdown",
                color: "var(--color-success)",
                bg: "var(--color-success-bg)",
              },
              {
                href: "/evals",
                icon: <IconChartBar size={18} stroke={1.6} />,
                label: "Evals",
                sub: "LLM quality scoring",
                color: "#7c3aed",
                bg: "#f5f3ff",
              },
            ].map(({ href, icon, label, sub, color, bg }) => (
              <Link key={href} href={href} style={{ textDecoration: "none" }}>
                <div
                  className="panel"
                  style={{ padding: "14px 16px", display: "flex", alignItems: "center", gap: 14, cursor: "pointer", transition: "box-shadow 0.15s ease" }}
                  onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "var(--shadow-card-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "var(--shadow-card)")}
                >
                  <div style={{ width: 36, height: 36, borderRadius: 9, background: bg, display: "flex", alignItems: "center", justifyContent: "center", color, flexShrink: 0 }}>
                    {icon}
                  </div>
                  <div>
                    <Text size="sm" fw={600}>{label}</Text>
                    <Text size="xs" c="dimmed">{sub}</Text>
                  </div>
                  <IconArrowRight size={14} style={{ marginLeft: "auto", color: "var(--color-text-tertiary)" }} />
                </div>
              </Link>
            ))}
          </div>
        </Grid.Col>
      </Grid>
    </div>
  );
}
