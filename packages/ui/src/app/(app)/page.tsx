"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Grid, Loader, RingProgress, Text } from "@mantine/core";
import { AreaChart } from "@mantine/charts";
import {
  IconCoin, IconBolt, IconShieldCheck, IconUsers,
  IconTimeline, IconCoins, IconChartBar,
  IconArrowRight, IconCheck, IconAlertCircle, IconAlertTriangle,
  IconTrendingUp,
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

const STATUS_COLOR: Record<string, string> = {
  ok: "var(--blue)", error: "var(--red)", drift: "var(--orange)", timeout: "var(--dark-grey)",
};
const STATUS_ICON: Record<string, React.ReactNode> = {
  ok:      <IconCheck size={11} />,
  error:   <IconAlertCircle size={11} />,
  drift:   <IconAlertTriangle size={11} />,
  timeout: <IconAlertCircle size={11} />,
};
const STATUS_LABEL: Record<string, string> = {
  ok: "pass", error: "fail", drift: "drift", timeout: "timeout",
};

// ---------------------------------------------------------------------------
// Health bar — AdminHub style status strip
// ---------------------------------------------------------------------------

function HealthBar({ traces }: { traces: TraceSummary[] }) {
  if (traces.length === 0) return null;
  const pass     = traces.filter((t) => t.status === "ok").length;
  const rate     = Math.round((pass / traces.length) * 100);
  const isGreen  = rate >= 90;
  const isYellow = rate >= 70 && !isGreen;

  const bg      = isGreen  ? "var(--light-green)"  : isYellow ? "var(--light-yellow)"  : "var(--light-red)";
  const border  = isGreen  ? "#a7f3d0"              : isYellow ? "#fde68a"              : "#fecaca";
  const accent  = isGreen  ? "var(--green)"         : isYellow ? "var(--yellow)"        : "var(--red)";
  const label   = isGreen  ? "All systems healthy"  : isYellow ? "Some agents degraded" : "Agents critical";

  return (
    <div style={{
      background: bg,
      border: `1px solid ${border}`,
      borderLeft: `4px solid ${accent}`,
      borderRadius: 14,
      padding: "12px 20px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 24,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 9, height: 9, borderRadius: "50%", background: accent }} />
        <span style={{ fontSize: 14, fontWeight: 600, color: accent }}>{label}</span>
        <span style={{ color: "var(--dark-grey)", fontSize: 13 }}>
          · {pass} of {traces.length} traces passing
        </span>
      </div>
      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 15, color: accent }}>
        {rate}%
      </span>
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
  const [offline, setOffline] = useState(false);

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
      setOffline(false);
    }).catch(() => {
      setOffline(true);
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

  if (offline) {
    return (
      <>
        <div className="page-head">
          <div className="page-head-left"><h1>Overview</h1></div>
        </div>
        <div style={{
          background: "var(--light-orange)",
          border: "1px solid #fed7aa",
          borderLeft: "4px solid var(--orange)",
          borderRadius: 14,
          padding: "18px 24px",
          display: "flex",
          alignItems: "flex-start",
          gap: 14,
        }}>
          <div style={{ fontSize: 22 }}>⚠️</div>
          <div>
            <div style={{ fontWeight: 700, color: "var(--orange)", marginBottom: 4 }}>Server offline</div>
            <div style={{ fontSize: 13, color: "var(--dark)", lineHeight: 1.6 }}>
              Could not connect to <code style={{ background: "#fee", padding: "1px 5px", borderRadius: 4 }}>localhost:8000</code>. Start the server then refresh.
            </div>
            <pre style={{ marginTop: 12, background: "#1a1a2e", color: "#a5f3fc", borderRadius: 8, padding: "10px 16px", fontSize: 12, overflowX: "auto" }}>{`set -a && source .env && set +a
.venv/bin/uvicorn app.main:app --reload --port 8000 --app-dir packages/server`}</pre>
          </div>
        </div>
      </>
    );
  }

  const today    = finops?.today;
  const allTime  = finops?.all_time;
  const passRate = evals?.pass_rate ?? null;
  const avgScore = evals?.avg_score ?? null;
  const agentCount = new Set(traces.map((t) => t.agent_name)).size;

  return (
    <>
      {/* Page heading */}
      <div className="page-head">
        <div className="page-head-left">
          <h1>Overview</h1>
          <ul className="breadcrumb">
            <li><span style={{ color: "var(--dark-grey)" }}>Argus</span></li>
            <li className="breadcrumb-sep">›</li>
            <li><span className="breadcrumb-active">Overview</span></li>
          </ul>
        </div>
        <span className={`live-badge ${status === "connected" ? "connected" : "disconnected"}`}>
          <span className="live-dot" />
          {status === "connected" ? "Live" : "Reconnecting…"}
        </span>
      </div>

      {/* Health strip */}
      <HealthBar traces={traces} />

      {/* KPI cards — AdminHub box-info style */}
      <ul className="box-info">
        <li className="box-info-item">
          <div className="box-info-icon blue">
            <IconCoin size={34} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3 className="mono">{fmtCost(today?.total_cost_usd ?? 0)}</h3>
            <p>Cost Today</p>
            {(allTime?.savings_usd ?? 0) > 0 && (
              <span className="sub" style={{ color: "var(--green)" }}>
                ↓ {fmtCost(allTime!.savings_usd)} saved
              </span>
            )}
          </div>
        </li>

        <li className="box-info-item">
          <div className="box-info-icon green">
            <IconBolt size={34} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3 className="mono">{fmtTokens(today?.local_tokens ?? 0)}</h3>
            <p>Local Tokens</p>
            <span className="sub">$0.00 · AMD hardware</span>
          </div>
        </li>

        <li className="box-info-item">
          <div className="box-info-icon violet">
            <IconShieldCheck size={34} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3>
              {passRate != null
                ? `${(passRate * 100).toFixed(0)}%`
                : traces.length > 0
                ? `${Math.round((traces.filter(t => t.status === "ok").length / traces.length) * 100)}%`
                : "—"}
            </h3>
            <p>Pass Rate</p>
            {avgScore != null && (
              <span className="sub">avg score {avgScore.toFixed(1)}</span>
            )}
          </div>
        </li>

        <li className="box-info-item">
          <div className="box-info-icon orange">
            <IconUsers size={34} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3>{agentCount}</h3>
            <p>Active Agents</p>
            <span className="sub">{today?.trace_count ?? traces.length} traces today</span>
          </div>
        </li>
      </ul>

      {/* Charts + Eval ring */}
      <div className="table-data" style={{ marginBottom: 24 }}>
        {/* Cost chart */}
        <div className="panel-block" style={{ flexGrow: 1, flexBasis: 500 }}>
          <div className="panel-block-head">
            <h3>Daily Cost</h3>
            <IconCoins size={18} color="var(--dark-grey)" />
          </div>
          {series.length === 0 ? (
            <Text size="sm" c="dimmed" ta="center" py={32}>
              No data yet — send some traces to see costs
            </Text>
          ) : (
            <AreaChart
              h={180}
              data={series}
              dataKey="date"
              series={[{ name: "total_cost_usd", label: "Cost ($)", color: "#3C91E6" }]}
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

        {/* Eval health */}
        <div className="panel-block" style={{ flexBasis: 260, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <div className="panel-block-head" style={{ alignSelf: "stretch" }}>
            <h3>Eval Health</h3>
            <IconChartBar size={18} color="var(--dark-grey)" />
          </div>
          {evals && (evals.total ?? 0) > 0 ? (
            <>
              <RingProgress
                size={130}
                thickness={11}
                roundCaps
                sections={[
                  { value: (passRate ?? 0) * 100, color: "#3C91E6" },
                  { value: (1 - (passRate ?? 0)) * 100, color: "#EEEEEE" },
                ]}
                label={
                  <Text ta="center" fw={700} size="xl" c="#3C91E6">
                    {passRate != null ? `${((passRate) * 100).toFixed(0)}%` : "—"}
                  </Text>
                }
              />
              <Text size="xs" c="dimmed" ta="center" mt={4}>{evals.total} evals scored</Text>
              {avgScore != null && (
                <Text size="xs" c="dimmed" ta="center">Avg {avgScore.toFixed(1)}/100</Text>
              )}
            </>
          ) : (
            <Text size="sm" c="dimmed" ta="center" py={20}>No evals yet</Text>
          )}
        </div>
      </div>

      {/* Recent traces + Quick nav */}
      <div className="table-data">
        {/* Recent traces */}
        <div className="panel-block" style={{ flexGrow: 1, flexBasis: 500 }}>
          <div className="panel-block-head">
            <h3>Recent Traces</h3>
            <IconTimeline size={18} color="var(--dark-grey)" />
            <Link href="/traces" style={{ fontSize: 12, color: "var(--blue)", fontWeight: 600, marginLeft: "auto", display: "flex", alignItems: "center", gap: 4 }}>
              View all <IconArrowRight size={12} />
            </Link>
          </div>

          {traces.length === 0 ? (
            <Text size="sm" c="dimmed" ta="center" py={24}>
              No traces yet. Instrument your agent with the Argus SDK.
            </Text>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["Status", "Agent", "Task", "Cost", "Time"].map((h) => (
                    <th key={h} style={{ paddingBottom: 10, fontSize: 11, fontWeight: 700, textAlign: "left", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--dark-grey)", borderBottom: "1px solid var(--grey)" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {traces.map((t) => (
                  <tr
                    key={t.trace_id}
                    style={{ cursor: "pointer" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--grey)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "")}
                  >
                    <td style={{ padding: "12px 0" }}>
                      <span
                        className="status-badge"
                        style={{ background: STATUS_COLOR[t.status] ?? "var(--dark-grey)" }}
                      >
                        {STATUS_LABEL[t.status] ?? t.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px 8px", fontSize: 13, fontWeight: 500 }}>{t.agent_name}</td>
                    <td style={{ padding: "12px 8px", fontSize: 12, color: "var(--dark-grey)", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {t.task ?? "—"}
                    </td>
                    <td style={{ padding: "12px 8px", fontSize: 12, fontFamily: "var(--font-mono)" }}>{fmtCost(t.total_cost_usd)}</td>
                    <td style={{ padding: "12px 0 12px 8px", fontSize: 12, color: "var(--dark-grey)", whiteSpace: "nowrap" }}>{timeAgo(t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Quick nav — AdminHub todo-list style */}
        <div className="panel-block" style={{ flexBasis: 280 }}>
          <div className="panel-block-head">
            <h3>Quick Access</h3>
            <IconTrendingUp size={18} color="var(--dark-grey)" />
          </div>
          <ul style={{ margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              { href: "/traces", icon: <IconTimeline size={18} />, label: "Traces",  sub: "Live execution logs", color: "var(--blue)", bg: "var(--light-blue)" },
              { href: "/finops", icon: <IconCoins size={18} />,    label: "FinOps",  sub: "Cost & savings",      color: "var(--green)", bg: "var(--light-green)" },
              { href: "/evals",  icon: <IconChartBar size={18} />, label: "Evals",   sub: "LLM quality scores",  color: "#7C3AED", bg: "var(--light-violet)" },
            ].map(({ href, icon, label, sub, color, bg }) => (
              <li key={href}>
                <Link href={href} style={{ textDecoration: "none" }}>
                  <div
                    style={{
                      background: "var(--grey)",
                      borderLeft: `6px solid ${color}`,
                      borderRadius: 10,
                      padding: "14px 16px",
                      display: "flex",
                      alignItems: "center",
                      gap: 14,
                      transition: "background 0.15s, transform 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.background = bg;
                      (e.currentTarget as HTMLElement).style.transform = "translateX(4px)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background = "var(--grey)";
                      (e.currentTarget as HTMLElement).style.transform = "";
                    }}
                  >
                    <div style={{ color }}>{icon}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--dark)" }}>{label}</div>
                      <div style={{ fontSize: 11, color: "var(--dark-grey)" }}>{sub}</div>
                    </div>
                    <IconArrowRight size={14} style={{ marginLeft: "auto", color: "var(--dark-grey)" }} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}
