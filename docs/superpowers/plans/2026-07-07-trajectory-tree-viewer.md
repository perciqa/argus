# Trajectory Tree Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the missing `traces/[id]` dedicated trace deep-dive page with an interactive waterfall timeline tree, plus a span detail panel.

**Architecture:** Custom waterfall tree component using Mantine primitives — a table where each row is a span node with depth indentation, expand/collapse chevrons, color-coded kind dots, horizontal duration bars, and inline token/cost badges. Clicking a span opens a slide-out detail panel. A "View full trace" button is added to the existing traces list drawer.

**Tech Stack:** Next.js 16 (App Router), React 19, Mantine v7, TypeScript, existing `@tabler/icons-react` icons. Zero new dependencies.

**Design spec:** `docs/superpowers/specs/2026-07-07-trajectory-tree-viewer-design.md`

---

## File Structure

```
packages/ui/src/
├── app/(app)/traces/[id]/
│   ├── page.tsx                    # Server component shell
│   ├── TraceDetailClient.tsx       # "use client" — data fetch, state, layout
│   └── components/
│       ├── TraceHeader.tsx         # Breadcrumb, title, stat cards
│       ├── WaterfallTree.tsx       # Table + toolbar, tree flattening logic
│       ├── WaterfallRow.tsx        # Single span row: bar, chevron, badges, depth
│       └── SpanDetailPanel.tsx     # Drawer panel with span I/O
├── app/(app)/traces/page.tsx       # ADD "View full trace" button in drawer (modify)
├── app/globals.css                 # ADD waterfall tree CSS classes
├── lib/api.ts                      # ADD extra fields to SpanRow type
└── lib/format.ts                   # CREATE shared formatting helpers
```

---

### Task 1: Extract shared formatting helpers to `lib/format.ts`

**Files:**
- Create: `packages/ui/src/lib/format.ts`
- Modify: `packages/ui/src/app/(app)/traces/page.tsx` (import from `@/lib/format` instead of local functions)

- [ ] **Step 1: Create `lib/format.ts`**

```typescript
export function fmtMs(ms: number | null) {
  if (ms == null) return "—";
  return ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(2)}s`;
}

export function fmtTokens(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function fmtCost(usd: number) {
  if (usd === 0) return "$0.00";
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  return `$${usd.toFixed(4)}`;
}

export function timeAgo(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}
```

- [ ] **Step 2: Update `traces/page.tsx` — remove local helpers, import from `@/lib/format`**

In `packages/ui/src/app/(app)/traces/page.tsx`, replace lines 17–39 (the four helper functions) with:
```typescript
import { fmtMs, fmtTokens, fmtCost, timeAgo } from "@/lib/format";
```

- [ ] **Step 3: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`
Expected: no errors related to format imports

- [ ] **Step 4: Commit**

```bash
git add packages/ui/src/lib/format.ts packages/ui/src/app/\(app\)/traces/page.tsx
git commit -m "refactor: extract formatting helpers to shared lib/format

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 2: Update SpanRow type with additional API fields

**Files:**
- Modify: `packages/ui/src/lib/api.ts`

- [ ] **Step 1: Replace the SpanRow interface in `api.ts`**

Replace lines 39–56:
```typescript
export interface SpanRow {
  span_id: string;
  trace_id: string;
  parent_span_id: string | null;
  name: string;
  kind: string;
  status: string;
  start_time: string;
  end_time: string | null;
  duration_ms: number | null;
  model_name: string | null;
  model_provider: string | null;
  model_base_url: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  model_cost_usd: number | null;
  model_latency_ms: number | null;
  model_cached: number | null;
  tool_name: string | null;
  tool_args_json: unknown | null;
  tool_result_json: unknown | null;
  tool_error: string | null;
  tool_latency_ms: number | null;
  input_json: unknown | null;
  output_json: unknown | null;
  attributes_json: Record<string, unknown> | null;
  events_json: unknown[] | null;
  error_message: string | null;
  error_type: string | null;
}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/lib/api.ts
git commit -m "feat: add extended span fields to SpanRow type for detail panel

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 3: Add waterfall tree CSS to globals.css

**Files:**
- Modify: `packages/ui/src/app/globals.css`

- [ ] **Step 1: Append CSS classes to end of `globals.css`**

```css
/* =========================================================
   WATERFALL TREE (traces/[id])
   ========================================================= */

.wf-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.wf-toolbar-btn {
  font-size: 11px;
  font-weight: 600;
  font-family: var(--lato);
  color: var(--dark-grey);
  background: var(--grey);
  border: none;
  border-radius: 6px;
  padding: 5px 12px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.wf-toolbar-btn:hover {
  background: var(--blue);
  color: var(--light);
}

.wf-table {
  width: 100%;
  border-collapse: collapse;
}

.wf-table th {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--dark-grey);
  border-bottom: 1px solid var(--grey);
  padding-bottom: 10px;
  text-align: left;
}

.wf-row {
  cursor: pointer;
  transition: background 0.12s;
  border-left: 3px solid transparent;
}

.wf-row:hover { background: var(--grey); }

.wf-row-selected {
  background: var(--light-blue) !important;
}

.wf-row-error {
  background: var(--light-red);
}

.wf-row-error:hover {
  background: #ffd6d4;
}

.wf-name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  min-height: 36px;
  position: relative;
}

.wf-chevron {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--dark-grey);
  flex-shrink: 0;
  padding: 0;
  border-radius: 3px;
  transition: background 0.12s;
}

.wf-chevron:hover { background: var(--grey); }

.wf-chevron-spacer {
  width: 18px;
  flex-shrink: 0;
}

.wf-span-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--dark);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.wf-sub-badge {
  font-size: 10px;
  font-weight: 600;
  font-family: var(--lato);
  padding: 1px 7px;
  border-radius: 10px;
  white-space: nowrap;
  flex-shrink: 0;
}

.wf-sub-badge.model { background: var(--light-violet); color: var(--violet); }
.wf-sub-badge.tool  { background: var(--light-orange); color: var(--orange); }
.wf-sub-badge.error { background: var(--light-red); color: var(--red); }

.wf-bar-wrap {
  flex: 1;
  height: 4px;
  background: var(--grey);
  border-radius: 2px;
  overflow: hidden;
  margin-left: 12px;
  min-width: 40px;
}

.wf-num {
  font-size: 12px;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  color: var(--dark-grey);
  padding: 8px 12px;
  white-space: nowrap;
}

.wf-empty {
  text-align: center;
  padding: 48px 0;
  color: var(--dark-grey);
  font-size: 13px;
}
```

- [ ] **Step 2: Commit**

```bash
git add packages/ui/src/app/globals.css
git commit -m "feat: add waterfall tree CSS classes

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 4: Create WaterfallRow component

**Files:**
- Create: `packages/ui/src/app/(app)/traces/[id]/components/WaterfallRow.tsx`

- [ ] **Step 1: Create directory**

```bash
mkdir -p "packages/ui/src/app/(app)/traces/[id]/components"
```

- [ ] **Step 2: Write `WaterfallRow.tsx`**

```typescript
"use client";

import { IconChevronRight, IconChevronDown } from "@tabler/icons-react";
import { Tooltip } from "@mantine/core";
import type { SpanRow } from "@/lib/api";
import { fmtMs, fmtTokens, fmtCost } from "@/lib/format";

const KIND_CLASS: Record<string, string> = {
  agent: "agent",
  model_call: "model_call",
  tool_call: "tool_call",
  internal: "internal",
  guardrail: "guardrail",
};

interface WaterfallRowProps {
  span: SpanRow;
  depth: number;
  maxDurationMs: number;
  hasChildren: boolean;
  expanded: boolean;
  onToggle: () => void;
  onSelect: () => void;
  selected: boolean;
}

export function WaterfallRow({
  span,
  depth,
  maxDurationMs,
  hasChildren,
  expanded,
  onToggle,
  onSelect,
  selected,
}: WaterfallRowProps) {
  const cls = KIND_CLASS[span.kind] ?? "internal";
  const pct = maxDurationMs > 0 ? Math.max(2, ((span.duration_ms ?? 0) / maxDurationMs) * 100) : 0;
  const tokens =
    span.completion_tokens != null
      ? span.completion_tokens
      : span.prompt_tokens;
  const isError = span.status === "error";

  return (
    <tr
      className={`wf-row ${isError ? "wf-row-error" : ""} ${selected ? "wf-row-selected" : ""}`}
      onClick={onSelect}
    >
      <td style={{ paddingLeft: depth * 24 + 8 }}>
        <div className="wf-name-cell">
          {hasChildren ? (
            <button
              className="wf-chevron"
              onClick={(e) => {
                e.stopPropagation();
                onToggle();
              }}
              aria-label={expanded ? "Collapse" : "Expand"}
            >
              {expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
            </button>
          ) : (
            <span className="wf-chevron-spacer" />
          )}
          <div className={`span-kind-dot ${cls}`} />
          <Tooltip label={span.name} disabled={span.name.length < 40} position="top-start" offset={8}>
            <span className="wf-span-name">{span.name}</span>
          </Tooltip>
          {span.model_name && <span className="wf-sub-badge model">{span.model_name}</span>}
          {span.tool_name && <span className="wf-sub-badge tool">{span.tool_name}</span>}
          {isError && (
            <Tooltip label={span.error_message ?? "Error"} disabled={!span.error_message} position="top" offset={8}>
              <span className="wf-sub-badge error">error</span>
            </Tooltip>
          )}
          <div className="wf-bar-wrap">
            <div
              className={`span-duration-bar ${cls}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      </td>
      <td className="mono wf-num">{fmtMs(span.duration_ms)}</td>
      <td className="mono wf-num">
        {tokens != null ? fmtTokens(tokens) : "—"}
      </td>
      <td className="mono wf-num">
        {span.model_cost_usd != null && span.model_cost_usd > 0
          ? fmtCost(span.model_cost_usd)
          : "—"}
      </td>
    </tr>
  );
}
```

- [ ] **Step 3: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 4: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/\[id\]/components/WaterfallRow.tsx
git commit -m "feat: add WaterfallRow component for trace detail tree

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 5: Create WaterfallTree component

**Files:**
- Create: `packages/ui/src/app/(app)/traces/[id]/components/WaterfallTree.tsx`

- [ ] **Step 1: Write `WaterfallTree.tsx`**

```typescript
"use client";

import { useMemo } from "react";
import { Text } from "@mantine/core";
import type { SpanRow } from "@/lib/api";
import { WaterfallRow } from "./WaterfallRow";

interface RenderNode {
  span: SpanRow;
  depth: number;
  hasChildren: boolean;
}

function flattenTree(spans: SpanRow[], collapsedIds: Set<string>): RenderNode[] {
  const childrenMap: Record<string, SpanRow[]> = {};
  spans.forEach((s) => {
    const pid = s.parent_span_id ?? "__root__";
    if (!childrenMap[pid]) childrenMap[pid] = [];
    childrenMap[pid].push(s);
  });

  Object.values(childrenMap).forEach((list) =>
    list.sort(
      (a, b) =>
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    )
  );

  const result: RenderNode[] = [];

  function walk(parentId: string, depth: number) {
    const kids = childrenMap[parentId] ?? [];
    kids.forEach((span) => {
      const hasKids = (childrenMap[span.span_id]?.length ?? 0) > 0;
      result.push({ span, depth, hasChildren: hasKids });
      if (!collapsedIds.has(span.span_id)) {
        walk(span.span_id, depth + 1);
      }
    });
  }

  walk("__root__", 0);
  return result;
}

interface WaterfallTreeProps {
  spans: SpanRow[];
  collapsedIds: Set<string>;
  onToggleCollapse: (spanId: string) => void;
  onCollapseAll: () => void;
  onExpandAll: () => void;
  selectedSpanId: string | null;
  onSelectSpan: (span: SpanRow) => void;
}

export function WaterfallTree({
  spans,
  collapsedIds,
  onToggleCollapse,
  onCollapseAll,
  onExpandAll,
  selectedSpanId,
  onSelectSpan,
}: WaterfallTreeProps) {
  const maxDurationMs = useMemo(
    () => Math.max(...spans.map((s) => s.duration_ms ?? 0), 1),
    [spans]
  );

  const nodes = useMemo(
    () => flattenTree(spans, collapsedIds),
    [spans, collapsedIds]
  );

  if (spans.length === 0) {
    return (
      <Text size="sm" c="dimmed" ta="center" className="wf-empty">
        No spans recorded for this trace.
      </Text>
    );
  }

  return (
    <>
      <div className="wf-toolbar">
        <button className="wf-toolbar-btn" onClick={onExpandAll}>
          Expand All
        </button>
        <button className="wf-toolbar-btn" onClick={onCollapseAll}>
          Collapse All
        </button>
      </div>

      <table className="wf-table">
        <thead>
          <tr>
            <th>Span</th>
            <th>Duration</th>
            <th>Tokens</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => (
            <WaterfallRow
              key={node.span.span_id}
              span={node.span}
              depth={node.depth}
              maxDurationMs={maxDurationMs}
              hasChildren={node.hasChildren}
              expanded={!collapsedIds.has(node.span.span_id)}
              onToggle={() => onToggleCollapse(node.span.span_id)}
              onSelect={() => onSelectSpan(node.span)}
              selected={selectedSpanId === node.span.span_id}
            />
          ))}
        </tbody>
      </table>
    </>
  );
}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/\[id\]/components/WaterfallTree.tsx
git commit -m "feat: add WaterfallTree component with expand/collapse

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 6: Create SpanDetailPanel component

**Files:**
- Create: `packages/ui/src/app/(app)/traces/[id]/components/SpanDetailPanel.tsx`

- [ ] **Step 1: Write `SpanDetailPanel.tsx`**

```typescript
"use client";

import { Drawer, Group, Text } from "@mantine/core";
import type { SpanRow } from "@/lib/api";
import { fmtMs, fmtTokens, fmtCost } from "@/lib/format";

interface SpanDetailPanelProps {
  span: SpanRow | null;
  opened: boolean;
  onClose: () => void;
}

type DetailRow = {
  label: string;
  value: string;
  mono?: boolean;
};

function collectDetails(span: SpanRow): DetailRow[] {
  const rows: DetailRow[] = [];

  rows.push({ label: "Span ID", value: span.span_id, mono: true });
  rows.push({ label: "Kind", value: span.kind.replace("_", " ") });
  rows.push({ label: "Status", value: span.status });

  if (span.start_time) {
    rows.push({
      label: "Start",
      value: new Date(span.start_time).toLocaleTimeString(),
      mono: true,
    });
  }
  if (span.end_time) {
    rows.push({
      label: "End",
      value: new Date(span.end_time).toLocaleTimeString(),
      mono: true,
    });
  }
  rows.push({ label: "Duration", value: fmtMs(span.duration_ms), mono: true });

  if (span.model_name) {
    rows.push({ label: "Model", value: span.model_name });
    if (span.model_provider) rows.push({ label: "Provider", value: span.model_provider });
    if (span.prompt_tokens != null) rows.push({ label: "Prompt Tokens", value: fmtTokens(span.prompt_tokens), mono: true });
    if (span.completion_tokens != null) rows.push({ label: "Completion Tokens", value: fmtTokens(span.completion_tokens), mono: true });
    if (span.model_cost_usd != null) rows.push({ label: "Cost", value: fmtCost(span.model_cost_usd), mono: true });
    if (span.model_latency_ms != null) rows.push({ label: "Model Latency", value: fmtMs(span.model_latency_ms), mono: true });
    if (span.model_cached != null) rows.push({ label: "Cached", value: span.model_cached === 1 ? "Yes" : "No" });
  }

  if (span.tool_name) {
    rows.push({ label: "Tool", value: span.tool_name });
    if (span.tool_error) rows.push({ label: "Tool Error", value: span.tool_error });
    if (span.tool_latency_ms != null) rows.push({ label: "Tool Latency", value: fmtMs(span.tool_latency_ms), mono: true });
  }

  if (span.error_message) {
    rows.push({ label: "Error", value: span.error_message });
  }
  if (span.error_type) {
    rows.push({ label: "Error Type", value: span.error_type });
  }

  return rows;
}

function DetailItem({ label, value, mono }: DetailRow) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        padding: "7px 0",
        borderBottom: "1px solid var(--grey)",
      }}
    >
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--dark-grey)",
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: 13,
          fontWeight: 500,
          fontFamily: mono ? "var(--font-mono)" : undefined,
          maxWidth: "60%",
          textAlign: "right",
          wordBreak: "break-all",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function JsonBlock({ label, data }: { label: string; data: unknown }) {
  const json =
    typeof data === "string"
      ? data
      : JSON.stringify(data, null, 2);

  return (
    <div style={{ marginTop: 16 }}>
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--dark-grey)",
          marginBottom: 6,
          display: "block",
        }}
      >
        {label}
      </span>
      <pre
        style={{
          fontSize: 11,
          fontFamily: "var(--font-mono)",
          background: "var(--grey)",
          borderRadius: 8,
          padding: "10px 14px",
          overflow: "auto",
          maxHeight: 300,
          whiteSpace: "pre-wrap",
          wordBreak: "break-all",
          margin: 0,
        }}
      >
        {json}
      </pre>
    </div>
  );
}

export function SpanDetailPanel({ span, opened, onClose }: SpanDetailPanelProps) {
  if (!span) return null;

  const details = collectDetails(span);
  const showInput  = span.input_json != null;
  const showOutput = span.output_json != null;
  const showToolArgs = span.tool_args_json != null;
  const showToolResult = span.tool_result_json != null;
  const showAttributes = span.attributes_json != null && Object.keys(span.attributes_json).length > 0;

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title={
        <Group gap="xs">
          <Text fw={700} size="sm" ff="var(--poppins)">
            {span.name}
          </Text>
          <span
            className="status-badge"
            style={{
              background:
                span.status === "ok"
                  ? "var(--blue)"
                  : span.status === "error"
                    ? "var(--red)"
                    : "var(--dark-grey)",
            }}
          >
            {span.status}
          </span>
        </Group>
      }
      position="right"
      size="lg"
      styles={{
        header: { borderBottom: "1px solid var(--grey)", paddingBottom: 12 },
        body: { paddingTop: 16, paddingLeft: 20, paddingRight: 20 },
      }}
    >
      <div style={{ fontFamily: "var(--poppins)" }}>
        {details.map((d) => (
          <DetailItem key={d.label} {...d} />
        ))}

        {showInput && <JsonBlock label="Input" data={span.input_json} />}
        {showOutput && <JsonBlock label="Output" data={span.output_json} />}
        {showToolArgs && <JsonBlock label="Tool Arguments" data={span.tool_args_json} />}
        {showToolResult && <JsonBlock label="Tool Result" data={span.tool_result_json} />}
        {showAttributes && <JsonBlock label="Attributes" data={span.attributes_json} />}
      </div>
    </Drawer>
  );
}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/\[id\]/components/SpanDetailPanel.tsx
git commit -m "feat: add SpanDetailPanel for span I/O inspection

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 7: Create TraceHeader component

**Files:**
- Create: `packages/ui/src/app/(app)/traces/[id]/components/TraceHeader.tsx`

- [ ] **Step 1: Write `TraceHeader.tsx`**

```typescript
"use client";

import Link from "next/link";
import {
  IconArrowLeft,
  IconCoin,
  IconBolt,
  IconClock,
  IconChartTree,
} from "@tabler/icons-react";
import type { TraceDetail } from "@/lib/api";
import { fmtMs, fmtTokens, fmtCost } from "@/lib/format";

interface EvalInfo {
  overall_score: number;
  verdict: string;
}

interface TraceHeaderProps {
  trace: TraceDetail;
  evalResult: EvalInfo | null;
}

const STATUS_BG: Record<string, string> = {
  ok: "var(--blue)",
  error: "var(--red)",
  drift: "var(--orange)",
  timeout: "var(--dark-grey)",
};
const STATUS_LABEL: Record<string, string> = {
  ok: "pass",
  error: "fail",
  drift: "drift",
  timeout: "timeout",
};

export function TraceHeader({ trace, evalResult }: TraceHeaderProps) {
  return (
    <>
      <div className="page-head">
        <div className="page-head-left">
          <h1>{trace.task ?? "Untitled trace"}</h1>
          <ul className="breadcrumb">
            <li>
              <Link
                href="/traces"
                style={{ color: "var(--dark-grey)", textDecoration: "none" }}
              >
                Traces
              </Link>
            </li>
            <li className="breadcrumb-sep">›</li>
            <li>
              <span className="breadcrumb-active">
                {trace.agent_name} / {trace.trace_id.slice(0, 8)}
              </span>
            </li>
          </ul>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            className="status-badge"
            style={{
              background: STATUS_BG[trace.status] ?? "var(--dark-grey)",
            }}
          >
            {STATUS_LABEL[trace.status] ?? trace.status}
          </span>
          {evalResult && (
            <span
              className="status-badge"
              style={{
                background:
                  evalResult.verdict === "pass"
                    ? "var(--blue)"
                    : evalResult.verdict === "fail"
                      ? "var(--red)"
                      : "var(--orange)",
              }}
            >
              eval {evalResult.overall_score.toFixed(1)}
            </span>
          )}
          <Link
            href="/traces"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 12,
              fontWeight: 600,
              color: "var(--blue)",
              textDecoration: "none",
            }}
          >
            <IconArrowLeft size={16} /> Back
          </Link>
        </div>
      </div>

      <ul className="box-info">
        <li className="box-info-item">
          <div className="box-info-icon blue">
            <IconClock size={32} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3 className="mono">{fmtMs(trace.duration_ms)}</h3>
            <p>Duration</p>
          </div>
        </li>
        <li className="box-info-item">
          <div className="box-info-icon green">
            <IconBolt size={32} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3 className="mono">{fmtTokens(trace.total_tokens)}</h3>
            <p>Total Tokens</p>
            <span className="sub">
              {fmtTokens(trace.local_tokens)} local / {fmtTokens(trace.cloud_tokens)} cloud
            </span>
          </div>
        </li>
        <li className="box-info-item">
          <div className="box-info-icon violet">
            <IconCoin size={32} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3 className="mono">{fmtCost(trace.total_cost_usd)}</h3>
            <p>Total Cost</p>
            <span className="sub">
              {trace.model_calls_count} model calls &middot; {trace.tool_calls_count} tool calls
            </span>
          </div>
        </li>
        <li className="box-info-item">
          <div className="box-info-icon orange">
            <IconChartTree size={32} stroke={1.6} />
          </div>
          <div className="box-info-text">
            <h3>{trace.spans.length}</h3>
            <p>Spans</p>
            <span className="sub">{trace.agent_name}</span>
          </div>
        </li>
      </ul>
    </>
  );
}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/\[id\]/components/TraceHeader.tsx
git commit -m "feat: add TraceHeader component with stat cards

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 8: Create TraceDetailClient page component

**Files:**
- Create: `packages/ui/src/app/(app)/traces/[id]/TraceDetailClient.tsx`

- [ ] **Step 1: Write `TraceDetailClient.tsx`**

```typescript
"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader, Text, Alert } from "@mantine/core";
import { IconAlertCircle, IconRefresh } from "@tabler/icons-react";
import { getTrace, type TraceDetail } from "@/lib/api";
import { useArgusWebSocket, type WsEvent } from "@/hooks/useArgusWebSocket";
import type { SpanRow } from "@/lib/api";
import { TraceHeader } from "./components/TraceHeader";
import { WaterfallTree } from "./components/WaterfallTree";
import { SpanDetailPanel } from "./components/SpanDetailPanel";

export function TraceDetailClient({ traceId }: { traceId: string }) {
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSpan, setSelectedSpan] = useState<SpanRow | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set());
  const [evalResult, setEvalResult] = useState<{
    overall_score: number;
    verdict: string;
  } | null>(null);

  const fetchTrace = useCallback(() => {
    setLoading(true);
    setError(null);
    getTrace(traceId)
      .then(setTrace)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [traceId]);

  useEffect(() => {
    fetchTrace();
  }, [fetchTrace]);

  useArgusWebSocket(
    useCallback(
      (event: WsEvent) => {
        if (event.event === "eval_complete") {
          const d = event.data as {
            trace_id?: string;
            overall_score?: number;
            verdict?: string;
          };
          if (d.trace_id === traceId) {
            setEvalResult({
              overall_score: d.overall_score ?? 0,
              verdict: d.verdict ?? "",
            });
          }
        }
      },
      [traceId]
    )
  );

  const handleSelectSpan = (span: SpanRow) => {
    setSelectedSpan(span);
    setDetailOpen(true);
  };

  const handleToggleCollapse = (spanId: string) => {
    setCollapsedIds((prev) => {
      const next = new Set(prev);
      if (next.has(spanId)) {
        next.delete(spanId);
      } else {
        next.add(spanId);
      }
      return next;
    });
  };

  const handleCollapseAll = () => {
    if (!trace) return;
    setCollapsedIds(new Set(trace.spans.map((s) => s.span_id)));
  };

  const handleExpandAll = () => {
    setCollapsedIds(new Set());
  };

  if (loading) {
    return (
      <div style={{ padding: 80, display: "flex", justifyContent: "center" }}>
        <Loader size="sm" color="blue" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "40px 0" }}>
        <Alert
          variant="light"
          color="red"
          title="Failed to load trace"
          icon={<IconAlertCircle size={16} />}
          style={{ marginBottom: 16 }}
        >
          {error}
        </Alert>
        <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
          <button
            className="wf-toolbar-btn"
            onClick={fetchTrace}
            style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
          >
            <IconRefresh size={14} /> Retry
          </button>
          <a
            href="/traces"
            className="wf-toolbar-btn"
            style={{ textDecoration: "none" }}
          >
            Back to Traces
          </a>
        </div>
      </div>
    );
  }

  if (!trace) {
    return (
      <div style={{ padding: "80px 0", textAlign: "center" }}>
        <Text size="lg" fw={600} c="var(--dark)">
          Trace not found
        </Text>
        <Text size="sm" c="dimmed" mt={8} mb={20}>
          The trace may have been deleted or the ID is incorrect.
        </Text>
        <a
          href="/traces"
          className="wf-toolbar-btn"
          style={{ textDecoration: "none" }}
        >
          Back to Traces
        </a>
      </div>
    );
  }

  return (
    <>
      <TraceHeader trace={trace} evalResult={evalResult} />

      <div className="table-data">
        <div className="panel-block" style={{ flexGrow: 1 }}>
          <div className="panel-block-head">
            <h3>Spans ({trace.spans.length})</h3>
          </div>

          <WaterfallTree
            spans={trace.spans}
            collapsedIds={collapsedIds}
            onToggleCollapse={handleToggleCollapse}
            onCollapseAll={handleCollapseAll}
            onExpandAll={handleExpandAll}
            selectedSpanId={selectedSpan?.span_id ?? null}
            onSelectSpan={handleSelectSpan}
          />
        </div>
      </div>

      <SpanDetailPanel
        span={selectedSpan}
        opened={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </>
  );
}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/\[id\]/TraceDetailClient.tsx
git commit -m "feat: add TraceDetailClient with data fetching and state management

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 9: Create traces/[id]/page.tsx route

**Files:**
- Create: `packages/ui/src/app/(app)/traces/[id]/page.tsx`

- [ ] **Step 1: Write `page.tsx`**

```typescript
import { TraceDetailClient } from "./TraceDetailClient";

export default async function TraceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <TraceDetailClient traceId={id} />;
}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/\[id\]/page.tsx
git commit -m "feat: add traces/[id] route page

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 10: Add "View full trace" link to traces drawer

**Files:**
- Modify: `packages/ui/src/app/(app)/traces/page.tsx`

- [ ] **Step 1: Add the "View full trace" button**

In `packages/ui/src/app/(app)/traces/page.tsx`, inside the Drawer body (after the SpanTimeline, at the end of the selected block, around line 326), add this block between the closing `</>` and `) : null`:

```tsx
{/* View full trace link */}
<div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid var(--grey)", textAlign: "center" }}>
  <a
    href={`/traces/${selected.trace_id}`}
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      fontSize: 12,
      fontWeight: 600,
      color: "var(--blue)",
      textDecoration: "none",
      padding: "6px 14px",
      borderRadius: 8,
      background: "var(--light-blue)",
      transition: "background 0.15s",
    }}
  >
    <IconTimeline size={16} /> View full trace
  </a>
</div>
```

The insertion point is right before `) : null` at the end of the selected conditional. The full changed section should look like:

```tsx
            <SpanTimeline spans={selected.spans} />

            {/* View full trace link */}
            <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid var(--grey)", textAlign: "center" }}>
              <a
                href={`/traces/${selected.trace_id}`}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  color: "var(--blue)",
                  textDecoration: "none",
                  padding: "6px 14px",
                  borderRadius: 8,
                  background: "var(--light-blue)",
                  transition: "background 0.15s",
                }}
              >
                <IconTimeline size={16} /> View full trace
              </a>
            </div>
          </>
        ) : null}
```

- [ ] **Step 2: Verify no compilation errors**

Run: `cd packages/ui && npx tsc --noEmit 2>&1 | head -30`

- [ ] **Step 3: Commit**

```bash
git add packages/ui/src/app/\(app\)/traces/page.tsx
git commit -m "feat: add View full trace link to traces drawer

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

### Task 11: Lint and verify

- [ ] **Step 1: Run TypeScript type check**

```bash
cd packages/ui && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 2: Run ESLint**

```bash
cd packages/ui && npx eslint src/ --ext .ts,.tsx 2>&1 | head -40
```
Expected: no errors (or only pre-existing warnings unrelated to new code).

- [ ] **Step 3: Run the Next.js build**

```bash
cd packages/ui && npm run build 2>&1 | tail -20
```
Expected: successful build.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: final lint and build verification pass

Co-authored-by: excelle <7961300+excelle@users.noreply.github.com>"
```

---

## Self-Review

**1. Spec coverage:**
- Page layout (trace header + waterfall tree + span detail panel): Tasks 4-9
- Data flow (fetch + WebSocket eval updates): Task 8
- Tree interactions (expand/collapse, select, waterfall bars): Tasks 4, 5
- Error states (loading, 404, API error, empty spans): Task 8
- Drawer → full page link: Task 10
- Component structure: Tasks 4-9
- CSS: Task 3
- Shared helpers: Task 1

**2. Placeholder scan:** No TBD/TODO/fill-in-later patterns. All code is complete.

**3. Type consistency:**
- `SpanRow` type updated in Task 2 matches usage in Tasks 4, 5, 6
- `TraceDetail` used in Tasks 7, 8 matches API type
- `fmtMs`, `fmtTokens`, `fmtCost` defined in Task 1, imported in Tasks 4, 6, 7
- `collapsedIds` state in Task 8 matches props in Task 5
- `selectedSpan` state in Task 8 matches props in Tasks 4, 6
