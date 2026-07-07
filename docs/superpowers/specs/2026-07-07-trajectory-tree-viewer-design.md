# Trajectory Tree Viewer — Design Spec

**Date:** 2026-07-07
**Status:** Approved
**Goal:** Implement the missing `traces/[id]` dedicated trace deep-dive page with an interactive waterfall timeline tree.

---

## 1. Overview

The current traces list shows span detail in a slide-out Drawer with a flat timeline. There is no way to deep-dive into a single trace with full tree structure, expand/collapse, and span I/O inspection. This feature builds a dedicated per-trace page at `traces/[id]` that serves both debugging (agent flow, span I/O) and performance analysis (duration bars, tokens, cost) use cases.

The existing Drawer on the traces list page is preserved for quick preview; a "View full trace" link navigates to the new deep-dive page.

---

## 2. Page Layout

### 2.1 Trace Header (top)

- Breadcrumb: `Traces > {agent_name} / {trace_id}`
- Title: `task` field or "Untitled trace"
- Summary stat row using `.box-info` pattern: status badge, total duration, total tokens, total cost, span count, model calls, tool calls
- Back button → `/traces`

### 2.2 Waterfall Tree (main area)

Full-width table with columns: Span Name, Duration, Tokens, Cost.

Each row is a span node rendering:
- Connector lines via CSS borders/pseudo-elements showing parent-child tree structure
- Horizontal duration bar proportional to `span.duration_ms / max_span_duration_in_trace * 100%`
- Colored span-kind indicator dot (agent=blue, model_call=violet, tool_call=green, guardrail=yellow, internal=grey)
- Expand/collapse chevron for spans with children
- Duration, token, and cost badges inline
- Error indicator for spans with `status: error`

Toolbar above tree: Collapse All / Expand All controls.

### 2.3 Span Detail Panel (side)

Opens on row click. Right-side slide-out panel (Mantine Drawer or inline panel) showing:
- Span name, kind, status, timing (start/end/duration)
- Input data (rendered as pre/code block)
- Output data (rendered as pre/code block)
- Model call details (if kind=model_call): model name, provider, prompt tokens, completion tokens, cached flag, latency
- Tool call details (if kind=tool_call): tool name, args JSON, result JSON, error, latency
- Error message + error_type (if status=error)
- Raw attributes and events (collapsed by default)

---

## 3. Data Flow & Interactions

### 3.1 Initial Load

1. Page mounts → fetch `GET /api/traces/{id}` → `TraceDetail` (trace summary + spans[])
2. Client-side builds tree: `parentSpanId → children[]` map from flat spans
3. Root nodes = spans with `parent_span_id: null`
4. Show Skeleton loader while fetching
5. On 404 → full-page "Trace not found" empty state with back link
6. On API error → error banner with retry button

### 3.2 WebSocket Updates

- `new_trace` event → ignored (user is viewing a specific trace)
- `eval_complete` event → if trace_id matches current page, update status badge and show eval score

### 3.3 Tree Interactions

- **Expand/collapse**: click chevron or span name → toggle children visibility via Mantine `Collapse` / `useDisclosure`
- **Collapse All / Expand All**: toolbar buttons set all nodes to collapsed/expanded
- **Select span**: click row → opens Span Detail Panel
- **Keyboard**: Arrow keys navigate between spans, Enter toggles expand, Space opens detail (ARIA treegrid pattern)
- **Waterfall bars**: width = `span.duration_ms / max_span_duration * 100%`, color-coded by kind, hover tooltip shows exact duration

### 3.4 Drawer → Full Page Link

Modify `traces/page.tsx` Drawer content: add "View full trace" button linking to `/traces/{trace_id}`.

---

## 4. Component Structure

### New files

```
packages/ui/src/app/(app)/traces/[id]/
├── page.tsx                    # Server component: renders client shell
├── TraceDetailClient.tsx       # "use client" — data fetch, state, layout
├── components/
│   ├── TraceHeader.tsx         # Breadcrumb, title, stat row, back button
│   ├── WaterfallTree.tsx       # Table + toolbar, builds tree from spans
│   ├── WaterfallRow.tsx        # Single span row: bar, chevron, badges, depth
│   └── SpanDetailPanel.tsx     # Slide-out panel with span I/O
```

### Modified files

- `traces/page.tsx` — add "View full trace" button in drawer
- `globals.css` — new CSS classes for tree connectors, depth indentation, row hover

### No changes needed

- `lib/api.ts` — `getTrace(id)` and types already exist
- `(app)/layout.tsx` — shell unchanged

### Dependencies

Zero new npm packages. All rendering uses Mantine v7 primitives already installed: `Card`, `Table`, `Group`, `Badge`, `Tooltip`, `Text`, `Drawer`, `Collapse`, `ActionIcon`, `Skeleton`, `Tabs`.

Existing CSS classes reused: `.page-head`, `.breadcrumb`, `.box-info`, `.status-badge`, `.span-kind-dot`, `.span-duration-bar`, `.mono`, `.table-data`, `.panel-block`.

---

## 5. Error & Edge States

| State | Handling |
|-------|----------|
| Loading | Skeleton placeholders for header stats + tree rows |
| 404 (trace not found) | Full-page empty state: icon, "Trace not found", description, back link |
| API error (500/network) | Red error banner at top with error message + Retry button |
| Empty spans array | Info banner: "No spans recorded for this trace" |
| Orphan span (no parent, parent not found) | Displayed as root-level node |
| Trace with 100+ spans | No virtualization needed; pagination already limits spans per trace at API level |
| Span with null duration | Show "—" instead of bar; bar width = 0 |
