#!/bin/sh
# Argus demo data seeder
# Sends 12 realistic traces across 4 agent types with mixed local/cloud spans
# Local:  bash scripts/seed_demo.sh
# Docker: sh /scripts/seed_demo.sh  (BASE set by compose env)

BASE="${BASE:-http://localhost:8000}"


send_trace() {
  local json="$1"
  curl -s -X POST "$BASE/api/traces" \
    -H "Content-Type: application/json" \
    -d "$json" | python3 -m json.tool 2>/dev/null | grep -E '"(trace_id|status)"'
  sleep 0.5
}

echo "🔵 Seeding Argus demo traces..."

# ── 1. data-analyst: full pass ──────────────────────────────────────────────
send_trace '{
  "trace_id":"demo-da-001","agent_name":"data-analyst","status":"ok",
  "task":"Generate monthly sales report for Q2 2026",
  "start_time":"2026-07-07T02:00:00Z","end_time":"2026-07-07T02:00:15Z",
  "duration_ms":15200,"total_tokens":12500,"total_cost_usd":0.0056,
  "local_tokens":3500,"cloud_tokens":9000,"model_calls_count":3,"tool_calls_count":2,
  "spans":[
    {"span_id":"da1-a","trace_id":"demo-da-001","name":"data-analyst","kind":"agent","status":"ok","start_time":"2026-07-07T02:00:00Z","end_time":"2026-07-07T02:00:15Z","duration_ms":15200},
    {"span_id":"da1-t1","trace_id":"demo-da-001","parent_span_id":"da1-a","name":"query_sales_db","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:00:01Z","end_time":"2026-07-07T02:00:03Z","duration_ms":2400,"tool_name":"query_sales_db"},
    {"span_id":"da1-m1","trace_id":"demo-da-001","parent_span_id":"da1-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"2026-07-07T02:00:03Z","end_time":"2026-07-07T02:00:04Z","duration_ms":800,"model_name":"accounts/fireworks/models/deepseek-v4-flash","prompt_tokens":1200,"completion_tokens":200,"model_cost_usd":0.000224},
    {"span_id":"da1-t2","trace_id":"demo-da-001","parent_span_id":"da1-a","name":"aggregate_data","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:00:04Z","end_time":"2026-07-07T02:00:06Z","duration_ms":1600,"tool_name":"aggregate_data"},
    {"span_id":"da1-m2","trace_id":"demo-da-001","parent_span_id":"da1-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:00:06Z","end_time":"2026-07-07T02:00:08Z","duration_ms":1800,"model_name":"gemma3:27b","prompt_tokens":2800,"completion_tokens":300,"model_cost_usd":0.0},
    {"span_id":"da1-m3","trace_id":"demo-da-001","parent_span_id":"da1-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"2026-07-07T02:00:08Z","end_time":"2026-07-07T02:00:09Z","duration_ms":1100,"model_name":"accounts/fireworks/models/deepseek-v4-flash","prompt_tokens":4500,"completion_tokens":500,"model_cost_usd":0.00077},
    {"span_id":"da1-t3","trace_id":"demo-da-001","parent_span_id":"da1-a","name":"generate_chart","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:00:09Z","end_time":"2026-07-07T02:00:10Z","duration_ms":1100,"tool_name":"generate_chart"}
  ]
}'

# ── 2. code-reviewer: pass ───────────────────────────────────────────────────
send_trace '{
  "trace_id":"demo-cr-001","agent_name":"code-reviewer","status":"ok",
  "task":"Review PR #127: refactor authentication middleware",
  "start_time":"2026-07-07T02:01:00Z","end_time":"2026-07-07T02:01:13Z",
  "duration_ms":12500,"total_tokens":8900,"total_cost_usd":0.0034,
  "local_tokens":4200,"cloud_tokens":4700,"model_calls_count":2,"tool_calls_count":3,
  "spans":[
    {"span_id":"cr1-a","trace_id":"demo-cr-001","name":"code-reviewer","kind":"agent","status":"ok","start_time":"2026-07-07T02:01:00Z","end_time":"2026-07-07T02:01:13Z","duration_ms":12500},
    {"span_id":"cr1-t1","trace_id":"demo-cr-001","parent_span_id":"cr1-a","name":"fetch_diff","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:01:01Z","end_time":"2026-07-07T02:01:02Z","duration_ms":800,"tool_name":"fetch_diff"},
    {"span_id":"cr1-m1","trace_id":"demo-cr-001","parent_span_id":"cr1-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:01:02Z","end_time":"2026-07-07T02:01:04Z","duration_ms":1900,"model_name":"gemma3:27b","prompt_tokens":3100,"completion_tokens":400,"model_cost_usd":0.0},
    {"span_id":"cr1-t2","trace_id":"demo-cr-001","parent_span_id":"cr1-a","name":"run_static_analysis","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:01:04Z","end_time":"2026-07-07T02:01:07Z","duration_ms":2800,"tool_name":"run_static_analysis"},
    {"span_id":"cr1-t3","trace_id":"demo-cr-001","parent_span_id":"cr1-a","name":"check_test_coverage","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:01:07Z","end_time":"2026-07-07T02:01:09Z","duration_ms":1600,"tool_name":"check_test_coverage"},
    {"span_id":"cr1-m2","trace_id":"demo-cr-001","parent_span_id":"cr1-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"2026-07-07T02:01:09Z","end_time":"2026-07-07T02:01:10Z","duration_ms":900,"model_name":"accounts/fireworks/models/deepseek-v4-flash","prompt_tokens":3500,"completion_tokens":400,"model_cost_usd":0.000602}
  ]
}'

# ── 3. customer-support: pass ─────────────────────────────────────────────────
send_trace '{
  "trace_id":"demo-cs-001","agent_name":"customer-support","status":"ok",
  "task":"Handle refund request for order #ORD-8821",
  "start_time":"2026-07-07T02:02:00Z","end_time":"2026-07-07T02:02:08Z",
  "duration_ms":8300,"total_tokens":4200,"total_cost_usd":0.0012,
  "local_tokens":4200,"cloud_tokens":0,"model_calls_count":2,"tool_calls_count":1,
  "spans":[
    {"span_id":"cs1-a","trace_id":"demo-cs-001","name":"customer-support","kind":"agent","status":"ok","start_time":"2026-07-07T02:02:00Z","end_time":"2026-07-07T02:02:08Z","duration_ms":8300},
    {"span_id":"cs1-m1","trace_id":"demo-cs-001","parent_span_id":"cs1-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:02:01Z","end_time":"2026-07-07T02:02:03Z","duration_ms":2100,"model_name":"gemma3:27b","prompt_tokens":1800,"completion_tokens":300,"model_cost_usd":0.0},
    {"span_id":"cs1-t1","trace_id":"demo-cs-001","parent_span_id":"cs1-a","name":"lookup_order","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:02:03Z","end_time":"2026-07-07T02:02:04Z","duration_ms":600,"tool_name":"lookup_order"},
    {"span_id":"cs1-m2","trace_id":"demo-cs-001","parent_span_id":"cs1-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:02:04Z","end_time":"2026-07-07T02:02:06Z","duration_ms":1900,"model_name":"gemma3:27b","prompt_tokens":1400,"completion_tokens":700,"model_cost_usd":0.0}
  ]
}'

# ── 4. customer-support: FAIL ─────────────────────────────────────────────────
send_trace '{
  "trace_id":"demo-cs-002","agent_name":"customer-support","status":"error",
  "task":"Cancel subscription for user@example.com",
  "start_time":"2026-07-07T02:03:00Z","end_time":"2026-07-07T02:03:05Z",
  "duration_ms":5200,"total_tokens":1800,"total_cost_usd":0.0,
  "local_tokens":1800,"cloud_tokens":0,"model_calls_count":1,"tool_calls_count":1,
  "spans":[
    {"span_id":"cs2-a","trace_id":"demo-cs-002","name":"customer-support","kind":"agent","status":"error","start_time":"2026-07-07T02:03:00Z","end_time":"2026-07-07T02:03:05Z","duration_ms":5200},
    {"span_id":"cs2-m1","trace_id":"demo-cs-002","parent_span_id":"cs2-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:03:00Z","end_time":"2026-07-07T02:03:02Z","duration_ms":1800,"model_name":"gemma3:27b","prompt_tokens":1200,"completion_tokens":600,"model_cost_usd":0.0},
    {"span_id":"cs2-t1","trace_id":"demo-cs-002","parent_span_id":"cs2-a","name":"cancel_subscription","kind":"tool_call","status":"error","start_time":"2026-07-07T02:03:02Z","end_time":"2026-07-07T02:03:05Z","duration_ms":2800,"tool_name":"cancel_subscription","error_message":"Billing API timeout after 2800ms"}
  ]
}'

# ── 5. research-agent: pass ───────────────────────────────────────────────────
send_trace '{
  "trace_id":"demo-ra-001","agent_name":"research-agent","status":"ok",
  "task":"Summarize AMD EPYC competitive advantages vs Intel Xeon",
  "start_time":"2026-07-07T02:04:00Z","end_time":"2026-07-07T02:04:06Z",
  "duration_ms":6200,"total_tokens":2100,"total_cost_usd":0.0,
  "local_tokens":2100,"cloud_tokens":0,"model_calls_count":2,"tool_calls_count":1,
  "spans":[
    {"span_id":"ra1-a","trace_id":"demo-ra-001","name":"research-agent","kind":"agent","status":"ok","start_time":"2026-07-07T02:04:00Z","end_time":"2026-07-07T02:04:06Z","duration_ms":6200},
    {"span_id":"ra1-t1","trace_id":"demo-ra-001","parent_span_id":"ra1-a","name":"web_search","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:04:01Z","end_time":"2026-07-07T02:04:02Z","duration_ms":800,"tool_name":"web_search"},
    {"span_id":"ra1-m1","trace_id":"demo-ra-001","parent_span_id":"ra1-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:04:02Z","end_time":"2026-07-07T02:04:06Z","duration_ms":3800,"model_name":"gemma3:27b","prompt_tokens":1400,"completion_tokens":700,"model_cost_usd":0.0}
  ]
}'

# ── 6. data-analyst: second run ───────────────────────────────────────────────
send_trace '{
  "trace_id":"demo-da-002","agent_name":"data-analyst","status":"ok",
  "task":"Generate weekly KPI dashboard for engineering team",
  "start_time":"2026-07-07T02:05:00Z","end_time":"2026-07-07T02:05:14Z",
  "duration_ms":14100,"total_tokens":11200,"total_cost_usd":0.0048,
  "local_tokens":4100,"cloud_tokens":7100,"model_calls_count":3,"tool_calls_count":2,
  "spans":[
    {"span_id":"da2-a","trace_id":"demo-da-002","name":"data-analyst","kind":"agent","status":"ok","start_time":"2026-07-07T02:05:00Z","end_time":"2026-07-07T02:05:14Z","duration_ms":14100},
    {"span_id":"da2-t1","trace_id":"demo-da-002","parent_span_id":"da2-a","name":"fetch_metrics","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:05:01Z","end_time":"2026-07-07T02:05:03Z","duration_ms":1900,"tool_name":"fetch_metrics"},
    {"span_id":"da2-m1","trace_id":"demo-da-002","parent_span_id":"da2-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"2026-07-07T02:05:03Z","end_time":"2026-07-07T02:05:05Z","duration_ms":2100,"model_name":"gemma3:27b","prompt_tokens":2800,"completion_tokens":350,"model_cost_usd":0.0},
    {"span_id":"da2-m2","trace_id":"demo-da-002","parent_span_id":"da2-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"2026-07-07T02:05:05Z","end_time":"2026-07-07T02:05:07Z","duration_ms":1100,"model_name":"accounts/fireworks/models/deepseek-v4-flash","prompt_tokens":3800,"completion_tokens":420,"model_cost_usd":0.000649},
    {"span_id":"da2-t2","trace_id":"demo-da-002","parent_span_id":"da2-a","name":"render_dashboard","kind":"tool_call","status":"ok","start_time":"2026-07-07T02:05:07Z","end_time":"2026-07-07T02:05:09Z","duration_ms":2300,"tool_name":"render_dashboard"},
    {"span_id":"da2-m3","trace_id":"demo-da-002","parent_span_id":"da2-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"2026-07-07T02:05:09Z","end_time":"2026-07-07T02:05:11Z","duration_ms":1300,"model_name":"accounts/fireworks/models/deepseek-v4-flash","prompt_tokens":4100,"completion_tokens":500,"model_cost_usd":0.000714}
  ]
}'

# ── 7-12. Batch: 2 more per agent ──────────────────────────────────────────────

for i in 3 4; do
  send_trace "{
    \"trace_id\":\"demo-da-00$i\",\"agent_name\":\"data-analyst\",\"status\":\"ok\",
    \"task\":\"Analyse churn cohort for segment $i\",
    \"start_time\":\"2026-07-07T02:0${i}:00Z\",\"end_time\":\"2026-07-07T02:0${i}:12Z\",
    \"duration_ms\":12000,\"total_tokens\":9800,\"total_cost_usd\":0.0041,
    \"local_tokens\":3200,\"cloud_tokens\":6600,\"model_calls_count\":2,\"tool_calls_count\":2,
    \"spans\":[
      {\"span_id\":\"da${i}-a\",\"trace_id\":\"demo-da-00$i\",\"name\":\"data-analyst\",\"kind\":\"agent\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:0${i}:00Z\",\"end_time\":\"2026-07-07T02:0${i}:12Z\",\"duration_ms\":12000},
      {\"span_id\":\"da${i}-t1\",\"trace_id\":\"demo-da-00$i\",\"parent_span_id\":\"da${i}-a\",\"name\":\"query_db\",\"kind\":\"tool_call\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:0${i}:01Z\",\"end_time\":\"2026-07-07T02:0${i}:03Z\",\"duration_ms\":2000,\"tool_name\":\"query_db\"},
      {\"span_id\":\"da${i}-m1\",\"trace_id\":\"demo-da-00$i\",\"parent_span_id\":\"da${i}-a\",\"name\":\"gemma3:27b\",\"kind\":\"model_call\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:0${i}:03Z\",\"end_time\":\"2026-07-07T02:0${i}:05Z\",\"duration_ms\":2200,\"model_name\":\"gemma3:27b\",\"prompt_tokens\":2800,\"completion_tokens\":400,\"model_cost_usd\":0.0}
    ]
  }"
done

for i in 2 3; do
  send_trace "{
    \"trace_id\":\"demo-cr-00$i\",\"agent_name\":\"code-reviewer\",\"status\":\"ok\",
    \"task\":\"Review PR #$((i * 50)): update dependency versions\",
    \"start_time\":\"2026-07-07T02:1${i}:00Z\",\"end_time\":\"2026-07-07T02:1${i}:11Z\",
    \"duration_ms\":11000,\"total_tokens\":7600,\"total_cost_usd\":0.0028,
    \"local_tokens\":3800,\"cloud_tokens\":3800,\"model_calls_count\":2,\"tool_calls_count\":2,
    \"spans\":[
      {\"span_id\":\"cr${i}-a\",\"trace_id\":\"demo-cr-00$i\",\"name\":\"code-reviewer\",\"kind\":\"agent\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:1${i}:00Z\",\"end_time\":\"2026-07-07T02:1${i}:11Z\",\"duration_ms\":11000},
      {\"span_id\":\"cr${i}-m1\",\"trace_id\":\"demo-cr-00$i\",\"parent_span_id\":\"cr${i}-a\",\"name\":\"gemma3:27b\",\"kind\":\"model_call\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:1${i}:01Z\",\"end_time\":\"2026-07-07T02:1${i}:03Z\",\"duration_ms\":2000,\"model_name\":\"gemma3:27b\",\"prompt_tokens\":2900,\"completion_tokens\":350,\"model_cost_usd\":0.0},
      {\"span_id\":\"cr${i}-m2\",\"trace_id\":\"demo-cr-00$i\",\"parent_span_id\":\"cr${i}-a\",\"name\":\"deepseek-v4\",\"kind\":\"model_call\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:1${i}:03Z\",\"end_time\":\"2026-07-07T02:1${i}:04Z\",\"duration_ms\":900,\"model_name\":\"accounts/fireworks/models/deepseek-v4-flash\",\"prompt_tokens\":3000,\"completion_tokens\":350,\"model_cost_usd\":0.000518}
    ]
  }"
done

for i in 3 4; do
  send_trace "{
    \"trace_id\":\"demo-cs-00$i\",\"agent_name\":\"customer-support\",\"status\":\"ok\",
    \"task\":\"Process return request #RET-$((i * 100))\",
    \"start_time\":\"2026-07-07T02:2${i}:00Z\",\"end_time\":\"2026-07-07T02:2${i}:08Z\",
    \"duration_ms\":8100,\"total_tokens\":3900,\"total_cost_usd\":0.0,
    \"local_tokens\":3900,\"cloud_tokens\":0,\"model_calls_count\":2,\"tool_calls_count\":1,
    \"spans\":[
      {\"span_id\":\"cs${i}-a\",\"trace_id\":\"demo-cs-00$i\",\"name\":\"customer-support\",\"kind\":\"agent\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:2${i}:00Z\",\"end_time\":\"2026-07-07T02:2${i}:08Z\",\"duration_ms\":8100},
      {\"span_id\":\"cs${i}-m1\",\"trace_id\":\"demo-cs-00$i\",\"parent_span_id\":\"cs${i}-a\",\"name\":\"gemma3:27b\",\"kind\":\"model_call\",\"status\":\"ok\",\"start_time\":\"2026-07-07T02:2${i}:01Z\",\"end_time\":\"2026-07-07T02:2${i}:03Z\",\"duration_ms\":1900,\"model_name\":\"gemma3:27b\",\"prompt_tokens\":1600,\"completion_tokens\":350,\"model_cost_usd\":0.0}
    ]
  }"
done

echo ""
echo "✅ Done! 12 traces seeded across 4 agents."
echo "   Open http://localhost:3000 to see the new design with real data."
echo ""
echo "   Local tokens:  free (AMD hardware)"
echo "   Cloud tokens:  Fireworks AI (DeepSeek V4 Flash)"
echo "   Mix:           ~50% local / 50% cloud — shows FinOps savings story"
