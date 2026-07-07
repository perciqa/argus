"use client";

import { useEffect, useState } from "react";
import { Badge, Card, Grid, Loader, Table, Text } from "@mantine/core";
import { LineChart } from "@mantine/charts";
import { listEvals, getEvalScores, type EvalSummary, type ScorePoint } from "@/lib/api";

function ScoreRing({ score }: { score: number }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const pct = score / 100;
  const color = score >= 70 ? "#059669" : score >= 50 ? "#d97706" : "#dc2626";

  return (
    <svg width={90} height={90} style={{ display: "block" }}>
      <circle cx={45} cy={45} r={r} fill="none" stroke="#f1f5f9" strokeWidth={8} />
      <circle
        cx={45} cy={45} r={r} fill="none"
        stroke={color} strokeWidth={8}
        strokeDasharray={circ}
        strokeDashoffset={circ * (1 - pct)}
        strokeLinecap="round"
        transform="rotate(-90 45 45)"
        style={{ transition: "stroke-dashoffset 0.8s ease" }}
      />
      <text x={45} y={49} textAnchor="middle" fontSize={18} fontWeight={700} fill={color}
            fontFamily="var(--font-inter)">
        {score.toFixed(0)}
      </text>
    </svg>
  );
}

const VERDICT_PROPS = {
  pass: { color: "green",  label: "Pass" },
  warn: { color: "orange", label: "Warn" },
  fail: { color: "red",    label: "Fail" },
};

function timeAgo(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60)   return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

export default function EvalsPage() {
  const [evals, setEvals]     = useState<EvalSummary[]>([]);
  const [scores, setScores]   = useState<ScorePoint[]>([]);
  const [total, setTotal]     = useState(0);
  const [avgScore, setAvgScore]   = useState<number | null>(null);
  const [passRate, setPassRate]   = useState<number | null>(null);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([listEvals(50), getEvalScores(7)]).then(([e, s]) => {
      setEvals(e.evals);
      setTotal(e.total);
      setAvgScore(e.avg_score);
      setPassRate(e.pass_rate);
      setScores(s);
    }).catch(() => { /* server offline */ }).finally(() => setLoading(false));

  }, []);

  if (loading) {
    return (
      <div className="page-container" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <Loader color="blue" />
      </div>
    );
  }

  const passCount = evals.filter((e) => e.verdict === "pass").length;
  const failCount = evals.filter((e) => e.verdict === "fail").length;
  const warnCount = evals.filter((e) => e.verdict === "warn").length;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Evals</h1>
        <p className="page-subtitle">Automated quality assessment · LLM judge via Fireworks AI · {total} evals</p>
      </div>

      {evals.length === 0 ? (
        <Card p="xl" ta="center">
          <Text size="sm" c="dimmed" mb={4}>No evals yet.</Text>
          <Text size="xs" c="dimmed">
            Evals run automatically in the background after each trace is ingested.
          </Text>
        </Card>
      ) : (
        <>
          {/* Score overview */}
          <Grid mb={24}>
            <Grid.Col span={3}>
              <Card p="md" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <Text className="stat-card-label" mb={8}>Avg Score</Text>
                {avgScore != null ? <ScoreRing score={avgScore} /> : <Text size="xl" fw={700}>—</Text>}
              </Card>
            </Grid.Col>
            <Grid.Col span={3}>
              <Card p="md">
                <Text className="stat-card-label">Pass Rate</Text>
                <div className="stat-card-value">
                  {passRate != null ? `${(passRate * 100).toFixed(0)}%` : "—"}
                </div>
                <Text size="xs" c="dimmed" mt={4}>{passCount} pass · {warnCount} warn · {failCount} fail</Text>
              </Card>
            </Grid.Col>
            <Grid.Col span={3}>
              <Card p="md">
                <Text className="stat-card-label">Total Evals</Text>
                <div className="stat-card-value">{total}</div>
                <Text size="xs" c="dimmed" mt={4}>Fireworks serverless · ~$0.00042/eval</Text>
              </Card>
            </Grid.Col>
            <Grid.Col span={3}>
              <Card p="md">
                <Text className="stat-card-label">Judge Model</Text>
                <div className="stat-card-value" style={{ fontSize: 14, marginTop: 8 }}>
                  {evals[0]?.judge_model ?? "gemma2:9b"}
                </div>
                <Badge variant="light" color="green" size="xs" mt={6}>Local · free</Badge>
              </Card>
            </Grid.Col>
          </Grid>

          {/* Score trend chart */}
          {scores.length > 0 && (
            <Card p="md" mb={24}>
              <Text size="sm" fw={600} mb={16}>Score Trend (7 days)</Text>
              <LineChart
                h={200}
                data={scores}
                dataKey="date"
                series={[{ name: "avg_score", label: "Avg score", color: "blue" }]}
                curveType="monotone"
                withDots={scores.length < 10}
                yAxisProps={{ domain: [0, 100] }}
                gridAxis="y"
                tickLine="none"
                referenceLines={[
                  { y: 70, label: "Pass threshold", color: "#059669" },
                  { y: 50, label: "Warn threshold", color: "#d97706" },
                ]}
              />
            </Card>
          )}

          {/* Evals table */}
          <Card p={0} style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>
              <Text size="sm" fw={600}>Recent Evals</Text>
            </div>
            <Table className="trace-table" horizontalSpacing="md" verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Verdict</Table.Th>
                  <Table.Th>Score</Table.Th>
                  <Table.Th>Agent</Table.Th>
                  <Table.Th>Explanation</Table.Th>
                  <Table.Th>When</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {evals.map((e) => {
                  const vp = VERDICT_PROPS[e.verdict] ?? VERDICT_PROPS.warn;
                  return (
                    <Table.Tr key={e.eval_id}>
                      <Table.Td>
                        <Badge color={vp.color} variant="light" size="sm">{vp.label}</Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" fw={600} className="mono"
                          c={e.overall_score >= 70 ? "green" : e.overall_score >= 50 ? "orange" : "red"}>
                          {e.overall_score.toFixed(1)}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{e.agent_name ?? "—"}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed" lineClamp={1} maw={320}>{e.explanation || "—"}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed">{timeAgo(e.evaluated_at)}</Text>
                      </Table.Td>
                    </Table.Tr>
                  );
                })}
              </Table.Tbody>
            </Table>
          </Card>
        </>
      )}
    </div>
  );
}
