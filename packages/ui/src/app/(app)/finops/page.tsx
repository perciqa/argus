"use client";

import { useEffect, useState } from "react";
import { Card, Grid, Loader, Table, Text, Tabs, Badge } from "@mantine/core";
import { AreaChart } from "@mantine/charts";
import {
  getFinOpsSummary, getTimeseries, getBreakdown,
  type FinOpsSummary, type TimeseriesPoint, type BreakdownResponse,
} from "@/lib/api";

function fmtCost(usd: number) {
  if (usd === 0) return "$0.00";
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  return `$${usd.toFixed(4)}`;
}

function fmtTokens(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function SumCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card p="md">
      <Text className="stat-card-label">{label}</Text>
      <div className="stat-card-value mono">{value}</div>
      {sub && <Text className="stat-card-delta" c="dimmed">{sub}</Text>}
    </Card>
  );
}

export default function FinOpsPage() {
  const [summary, setSummary]     = useState<FinOpsSummary | null>(null);
  const [series, setSeries]       = useState<TimeseriesPoint[]>([]);
  const [breakdown, setBreakdown] = useState<BreakdownResponse | null>(null);
  const [loading, setLoading]     = useState(true);
  const [days, setDays]           = useState("7");

  useEffect(() => {
    Promise.all([
      getFinOpsSummary(),
      getTimeseries(Number(days)),
      getBreakdown(),
    ]).then(([s, ts, b]) => {
      setSummary(s);
      setSeries(ts);
      setBreakdown(b);
    }).finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return (
      <div className="page-container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <Loader color="blue" />
      </div>
    );
  }

  const today    = summary?.today;
  const allTime  = summary?.all_time;
  const thisWeek = summary?.this_week;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">FinOps</h1>
        <p className="page-subtitle">Cost tracking and local inference savings</p>
      </div>

      {/* Savings alert */}
      {(allTime?.savings_usd ?? 0) > 0 && (
        <div className="savings-alert" role="status">
          <span>💰</span>
          <span>
            You saved{" "}
            <span className="savings-amount">{fmtCost(allTime!.savings_usd)}</span>{" "}
            all time by running locally on AMD hardware instead of cloud APIs.
          </span>
        </div>
      )}

      {/* Today summary */}
      <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={10}>Today</Text>
      <div className="stat-cards-row" style={{ marginBottom: 28 }}>
        <SumCard label="Total Cost"        value={fmtCost(today?.total_cost_usd ?? 0)} />
        <SumCard label="Local Tokens"      value={fmtTokens(today?.local_tokens ?? 0)}  sub="$0.00 (free)" />
        <SumCard label="Cloud Tokens"      value={fmtTokens(today?.cloud_tokens ?? 0)} />
        <SumCard label="Traces"            value={String(today?.trace_count ?? 0)} />
      </div>

      {/* This week / All time */}
      <Grid mb={28}>
        <Grid.Col span={6}>
          <Card p="md">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={12}>This Week</Text>
            <Grid gutter="xs">
              <Grid.Col span={6}><Text size="xs" c="dimmed">Cost</Text><Text fw={600} className="mono">{fmtCost(thisWeek?.total_cost_usd ?? 0)}</Text></Grid.Col>
              <Grid.Col span={6}><Text size="xs" c="dimmed">Savings</Text><Text fw={600} c="green" className="mono">{fmtCost(thisWeek?.savings_usd ?? 0)}</Text></Grid.Col>
              <Grid.Col span={6}><Text size="xs" c="dimmed">Local tokens</Text><Text fw={600} className="mono">{fmtTokens(thisWeek?.local_tokens ?? 0)}</Text></Grid.Col>
              <Grid.Col span={6}><Text size="xs" c="dimmed">Traces</Text><Text fw={600}>{thisWeek?.trace_count ?? 0}</Text></Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>
        <Grid.Col span={6}>
          <Card p="md">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={12}>All Time</Text>
            <Grid gutter="xs">
              <Grid.Col span={6}><Text size="xs" c="dimmed">Cost</Text><Text fw={600} className="mono">{fmtCost(allTime?.total_cost_usd ?? 0)}</Text></Grid.Col>
              <Grid.Col span={6}><Text size="xs" c="dimmed">Savings</Text><Text fw={600} c="green" className="mono">{fmtCost(allTime?.savings_usd ?? 0)}</Text></Grid.Col>
              <Grid.Col span={6}><Text size="xs" c="dimmed">Local tokens</Text><Text fw={600} className="mono">{fmtTokens(allTime?.local_tokens ?? 0)}</Text></Grid.Col>
              <Grid.Col span={6}><Text size="xs" c="dimmed">Traces</Text><Text fw={600}>{allTime?.trace_count ?? 0}</Text></Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Cost chart */}
      <Card p="md" mb={24}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <Text size="sm" fw={600}>Daily Cost</Text>
          <Tabs value={days} onChange={(v) => v && setDays(v)} variant="pills" radius="sm">
            <Tabs.List>
              {["7", "14", "30"].map((d) => (
                <Tabs.Tab key={d} value={d} py={4} px={10}>
                  <Text size="xs">{d}d</Text>
                </Tabs.Tab>
              ))}
            </Tabs.List>
          </Tabs>
        </div>
        {series.length === 0 ? (
          <Text size="sm" c="dimmed" ta="center" py={40}>No data yet</Text>
        ) : (
          <AreaChart
            h={220}
            data={series}
            dataKey="date"
            series={[
              { name: "total_cost_usd", label: "Total cost ($)", color: "blue" },
            ]}
            curveType="monotone"
            withLegend={false}
            withDots={series.length < 10}
            gridAxis="y"
            tickLine="none"
            valueFormatter={(v) => fmtCost(v as number)}
          />
        )}
      </Card>

      {/* Breakdown tables */}
      <Grid>
        <Grid.Col span={6}>
          <Card p={0} style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>
              <Text size="sm" fw={600}>By Agent</Text>
            </div>
            <Table className="trace-table" horizontalSpacing="md" verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Agent</Table.Th>
                  <Table.Th>Traces</Table.Th>
                  <Table.Th>Cost</Table.Th>
                  <Table.Th>Local tokens</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {breakdown?.by_agent.length === 0 && (
                  <Table.Tr><Table.Td colSpan={4}><Text size="sm" c="dimmed" py="sm">No data</Text></Table.Td></Table.Tr>
                )}
                {breakdown?.by_agent.map((r) => (
                  <Table.Tr key={r.agent_name}>
                    <Table.Td><Text size="sm" fw={500}>{r.agent_name}</Text></Table.Td>
                    <Table.Td><Text size="sm" className="mono">{r.trace_count}</Text></Table.Td>
                    <Table.Td><Text size="sm" className="mono">{fmtCost(r.total_cost_usd)}</Text></Table.Td>
                    <Table.Td><Text size="sm" className="mono" c="green">{fmtTokens(r.local_tokens)}</Text></Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Grid.Col>

        <Grid.Col span={6}>
          <Card p={0} style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>
              <Text size="sm" fw={600}>By Model</Text>
            </div>
            <Table className="trace-table" horizontalSpacing="md" verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Model</Table.Th>
                  <Table.Th>Provider</Table.Th>
                  <Table.Th>Calls</Table.Th>
                  <Table.Th>Cost</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {breakdown?.by_model.length === 0 && (
                  <Table.Tr><Table.Td colSpan={4}><Text size="sm" c="dimmed" py="sm">No data</Text></Table.Td></Table.Tr>
                )}
                {breakdown?.by_model.map((r, i) => (
                  <Table.Tr key={i}>
                    <Table.Td><Text size="sm" className="mono">{r.model_name}</Text></Table.Td>
                    <Table.Td>
                      <Badge variant="outline" size="xs" color={r.model_provider === "local" ? "green" : "gray"}>
                        {r.model_provider}
                      </Badge>
                    </Table.Td>
                    <Table.Td><Text size="sm" className="mono">{r.call_count}</Text></Table.Td>
                    <Table.Td><Text size="sm" className="mono">{fmtCost(r.total_cost_usd)}</Text></Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Grid.Col>
      </Grid>
    </div>
  );
}
