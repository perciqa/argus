#!/bin/sh
# Argus demo data seeder
# Seeds 12 traces that tell a coherent narrative across 4 agents.
# Traces are ordered for the story arc:
#   success → cost savings → error detection → safety → quality scoring
#
# Local:  bash scripts/seed_demo.sh
# Docker: sh /scripts/seed_demo.sh  (BASE set by compose env)

BASE="${BASE:-http://localhost:8000}"

send_trace() {
  local json="$1"
  curl -s -X POST "$BASE/api/traces" \
    -H "Content-Type: application/json" \
    -d "$json" > /dev/null
  sleep 0.3
}

echo "🔵 Seeding Argus demo traces..."

TODAY=$(date -u +"%Y-%m-%d")

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 1 — Success: customer support handles refund, all-local, $0.00
# Story beat: "Your agent works. Local model. Zero cost."
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-01-refund","agent_name":"customer-support","status":"ok",
  "task":"Handle refund request for order ORD-8821 — customer received damaged item",
  "start_time":"'"$TODAY"'T09:00:00Z","end_time":"'"$TODAY"'T09:00:08Z",
  "duration_ms":8300,"total_tokens":4200,"total_cost_usd":0.0,
  "local_tokens":4200,"cloud_tokens":0,"model_calls_count":2,"tool_calls_count":1,
  "spans":[
    {"span_id":"s01-a","trace_id":"seed-01-refund","name":"customer-support","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:00:00Z","end_time":"'"$TODAY"'T09:00:08Z","duration_ms":8300},
    {"span_id":"s01-m1","trace_id":"seed-01-refund","parent_span_id":"s01-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:00:01Z","end_time":"'"$TODAY"'T09:00:03Z","duration_ms":2100,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":1800,"completion_tokens":300,"model_cost_usd":0.0},
    {"span_id":"s01-t1","trace_id":"seed-01-refund","parent_span_id":"s01-a","name":"lookup_order","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:00:03Z","end_time":"'"$TODAY"'T09:00:04Z","duration_ms":600,"tool_name":"lookup_order"},
    {"span_id":"s01-m2","trace_id":"seed-01-refund","parent_span_id":"s01-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:00:04Z","end_time":"'"$TODAY"'T09:00:06Z","duration_ms":1900,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":1400,"completion_tokens":700,"model_cost_usd":0.0}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 2 — Success: research with AMD-friendly story, multi-model routing
# Story beat: "Agent routes to right model. Cloud for complex, local for simple."
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-02-amd-bench","agent_name":"research-agent","status":"ok",
  "task":"Compare AMD MI300X vs NVIDIA H100 inference benchmarks for LLM serving",
  "start_time":"'"$TODAY"'T09:05:00Z","end_time":"'"$TODAY"'T09:05:15Z",
  "duration_ms":15200,"total_tokens":12500,"total_cost_usd":0.0042,
  "local_tokens":3500,"cloud_tokens":9000,"model_calls_count":3,"tool_calls_count":2,
  "spans":[
    {"span_id":"s02-a","trace_id":"seed-02-amd-bench","name":"research-agent","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:05:00Z","end_time":"'"$TODAY"'T09:05:15Z","duration_ms":15200},
    {"span_id":"s02-r1","trace_id":"seed-02-amd-bench","parent_span_id":"s02-a","name":"classify_task","kind":"reason","status":"ok","start_time":"'"$TODAY"'T09:05:01Z","end_time":"'"$TODAY"'T09:05:03Z","duration_ms":1800},
    {"span_id":"s02-t1","trace_id":"seed-02-amd-bench","parent_span_id":"s02-a","name":"search_benchmarks","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:05:03Z","end_time":"'"$TODAY"'T09:05:05Z","duration_ms":2400,"tool_name":"search_benchmarks"},
    {"span_id":"s02-m1","trace_id":"seed-02-amd-bench","parent_span_id":"s02-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:05:05Z","end_time":"'"$TODAY"'T09:05:07Z","duration_ms":1800,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":2800,"completion_tokens":350,"model_cost_usd":0.0},
    {"span_id":"s02-m2","trace_id":"seed-02-amd-bench","parent_span_id":"s02-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:05:07Z","end_time":"'"$TODAY"'T09:05:09Z","duration_ms":1100,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":4500,"completion_tokens":500,"model_cost_usd":0.00077},
    {"span_id":"s02-t2","trace_id":"seed-02-amd-bench","parent_span_id":"s02-a","name":"generate_chart","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:05:09Z","end_time":"'"$TODAY"'T09:05:11Z","duration_ms":1100,"tool_name":"generate_chart"},
    {"span_id":"s02-m3","trace_id":"seed-02-amd-bench","parent_span_id":"s02-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:05:11Z","end_time":"'"$TODAY"'T09:05:12Z","duration_ms":800,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":4100,"completion_tokens":450,"model_cost_usd":0.000714}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 3 — Success: finops calculation, cloud model with real cost
# Story beat: "Not everything is free. Cloud costs tracked per-call."
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-03-finops","agent_name":"data-analyst","status":"ok",
  "task":"Calculate TCO savings: hybrid routing with AMD local GPUs saves 68% vs all-cloud",
  "start_time":"'"$TODAY"'T09:10:00Z","end_time":"'"$TODAY"'T09:10:12Z",
  "duration_ms":12000,"total_tokens":9800,"total_cost_usd":0.0041,
  "local_tokens":3200,"cloud_tokens":6600,"model_calls_count":2,"tool_calls_count":2,
  "spans":[
    {"span_id":"s03-a","trace_id":"seed-03-finops","name":"data-analyst","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:10:00Z","end_time":"'"$TODAY"'T09:10:12Z","duration_ms":12000},
    {"span_id":"s03-r1","trace_id":"seed-03-finops","parent_span_id":"s03-a","name":"classify_task","kind":"reason","status":"ok","start_time":"'"$TODAY"'T09:10:01Z","end_time":"'"$TODAY"'T09:10:02Z","duration_ms":1400},
    {"span_id":"s03-t1","trace_id":"seed-03-finops","parent_span_id":"s03-a","name":"calculate_tco","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:10:02Z","end_time":"'"$TODAY"'T09:10:04Z","duration_ms":2000,"tool_name":"calculate_tco"},
    {"span_id":"s03-m1","trace_id":"seed-03-finops","parent_span_id":"s03-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:10:04Z","end_time":"'"$TODAY"'T09:10:06Z","duration_ms":2200,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":2800,"completion_tokens":400,"model_cost_usd":0.0},
    {"span_id":"s03-m2","trace_id":"seed-03-finops","parent_span_id":"s03-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:10:06Z","end_time":"'"$TODAY"'T09:10:08Z","duration_ms":1300,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":3200,"completion_tokens":380,"model_cost_usd":0.000554}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 4 — ERROR: missing order ORD-9999 (THE HERO MOMENT)
# Story beat: "Agent returned 200 OK. Argus caught the failed tool call inside."
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-04-ord9999","agent_name":"customer-support","status":"error",
  "task":"Check order status for ORD-9999",
  "start_time":"'"$TODAY"'T09:15:00Z","end_time":"'"$TODAY"'T09:15:05Z",
  "duration_ms":5200,"total_tokens":1800,"total_cost_usd":0.0,
  "local_tokens":1800,"cloud_tokens":0,"model_calls_count":1,"tool_calls_count":1,
  "error_message":"Tool call failed: lookup_order returned database error",
  "spans":[
    {"span_id":"s04-a","trace_id":"seed-04-ord9999","name":"customer-support","kind":"agent","status":"error","start_time":"'"$TODAY"'T09:15:00Z","end_time":"'"$TODAY"'T09:15:05Z","duration_ms":5200},
    {"span_id":"s04-r1","trace_id":"seed-04-ord9999","parent_span_id":"s04-a","name":"classify_task","kind":"reason","status":"ok","start_time":"'"$TODAY"'T09:15:01Z","end_time":"'"$TODAY"'T09:15:02Z","duration_ms":1200},
    {"span_id":"s04-m1","trace_id":"seed-04-ord9999","parent_span_id":"s04-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:15:02Z","end_time":"'"$TODAY"'T09:15:03Z","duration_ms":800,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":1200,"completion_tokens":600,"model_cost_usd":0.0},
    {"span_id":"s04-t1","trace_id":"seed-04-ord9999","parent_span_id":"s04-a","name":"lookup_order","kind":"tool_call","status":"error","start_time":"'"$TODAY"'T09:15:03Z","end_time":"'"$TODAY"'T09:15:05Z","duration_ms":2800,"tool_name":"lookup_order","tool_error":"Billing API timeout after 2800ms","error_message":"Billing API timeout after 2800ms"}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 5 — Safety: guardrail triggers, escalation
# Story beat: "Guardrails catch unsafe requests. Agent escalates to human."
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-05-guardrail","agent_name":"customer-support","status":"ok",
  "task":"Customer requests deletion of all billing records — escalation required",
  "start_time":"'"$TODAY"'T09:20:00Z","end_time":"'"$TODAY"'T09:20:04Z",
  "duration_ms":4200,"total_tokens":1100,"total_cost_usd":0.0,
  "local_tokens":1100,"cloud_tokens":0,"model_calls_count":1,"tool_calls_count":0,
  "spans":[
    {"span_id":"s05-a","trace_id":"seed-05-guardrail","name":"customer-support","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:20:00Z","end_time":"'"$TODAY"'T09:20:04Z","duration_ms":4200},
    {"span_id":"s05-g1","trace_id":"seed-05-guardrail","parent_span_id":"s05-a","name":"pii_guardrail","kind":"guardrail","status":"ok","start_time":"'"$TODAY"'T09:20:01Z","end_time":"'"$TODAY"'T09:20:02Z","duration_ms":600},
    {"span_id":"s05-m1","trace_id":"seed-05-guardrail","parent_span_id":"s05-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:20:02Z","end_time":"'"$TODAY"'T09:20:03Z","duration_ms":800,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":700,"completion_tokens":400,"model_cost_usd":0.0},
    {"span_id":"s05-r1","trace_id":"seed-05-guardrail","parent_span_id":"s05-a","name":"escalate_to_human","kind":"internal","status":"ok","start_time":"'"$TODAY"'T09:20:03Z","end_time":"'"$TODAY"'T09:20:04Z","duration_ms":500}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 6 — Code review: success with mixed local/cloud
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-06-pr","agent_name":"code-reviewer","status":"ok",
  "task":"Review PR #312: refactor authentication middleware with async support",
  "start_time":"'"$TODAY"'T09:25:00Z","end_time":"'"$TODAY"'T09:25:13Z",
  "duration_ms":12500,"total_tokens":8900,"total_cost_usd":0.0034,
  "local_tokens":4200,"cloud_tokens":4700,"model_calls_count":2,"tool_calls_count":3,
  "spans":[
    {"span_id":"s06-a","trace_id":"seed-06-pr","name":"code-reviewer","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:25:00Z","end_time":"'"$TODAY"'T09:25:13Z","duration_ms":12500},
    {"span_id":"s06-t1","trace_id":"seed-06-pr","parent_span_id":"s06-a","name":"fetch_diff","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:25:01Z","end_time":"'"$TODAY"'T09:25:02Z","duration_ms":800,"tool_name":"fetch_diff"},
    {"span_id":"s06-m1","trace_id":"seed-06-pr","parent_span_id":"s06-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:25:02Z","end_time":"'"$TODAY"'T09:25:04Z","duration_ms":1900,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":3100,"completion_tokens":400,"model_cost_usd":0.0},
    {"span_id":"s06-t2","trace_id":"seed-06-pr","parent_span_id":"s06-a","name":"run_static_analysis","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:25:04Z","end_time":"'"$TODAY"'T09:25:07Z","duration_ms":2800,"tool_name":"run_static_analysis"},
    {"span_id":"s06-t3","trace_id":"seed-06-pr","parent_span_id":"s06-a","name":"check_test_coverage","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:25:07Z","end_time":"'"$TODAY"'T09:25:09Z","duration_ms":1600,"tool_name":"check_test_coverage"},
    {"span_id":"s06-m2","trace_id":"seed-06-pr","parent_span_id":"s06-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:25:09Z","end_time":"'"$TODAY"'T09:25:10Z","duration_ms":900,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":3500,"completion_tokens":400,"model_cost_usd":0.000602}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 7 — Drift warning: agent quality regression over time
# ══════════════════════════════════════════════════════════════════════════════
send_trace '{
  "trace_id":"seed-07-drift","agent_name":"research-agent","status":"drift",
  "task":"Summarize latest EU AI Act compliance requirements for agent deployments",
  "start_time":"'"$TODAY"'T09:30:00Z","end_time":"'"$TODAY"'T09:30:09Z",
  "duration_ms":9200,"total_tokens":5600,"total_cost_usd":0.0018,
  "local_tokens":5600,"cloud_tokens":0,"model_calls_count":2,"tool_calls_count":1,
  "spans":[
    {"span_id":"s07-a","trace_id":"seed-07-drift","name":"research-agent","kind":"agent","status":"drift","start_time":"'"$TODAY"'T09:30:00Z","end_time":"'"$TODAY"'T09:30:09Z","duration_ms":9200},
    {"span_id":"s07-t1","trace_id":"seed-07-drift","parent_span_id":"s07-a","name":"web_search","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:30:01Z","end_time":"'"$TODAY"'T09:30:03Z","duration_ms":1800,"tool_name":"web_search"},
    {"span_id":"s07-m1","trace_id":"seed-07-drift","parent_span_id":"s07-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:30:03Z","end_time":"'"$TODAY"'T09:30:05Z","duration_ms":1900,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":3400,"completion_tokens":400,"model_cost_usd":0.0},
    {"span_id":"s07-m2","trace_id":"seed-07-drift","parent_span_id":"s07-a","name":"gemma3:27b","kind":"model_call","status":"drift","start_time":"'"$TODAY"'T09:30:05Z","end_time":"'"$TODAY"'T09:30:08Z","duration_ms":3200,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":1800,"completion_tokens":200,"model_cost_usd":0.0,"error_message":"Output factual accuracy below threshold — hallucinated regulation date"}
  ]
}'

# ══════════════════════════════════════════════════════════════════════════════
# TRACE 8–12: Fill with more success/fail variety
# ══════════════════════════════════════════════════════════════════════════════

send_trace '{
  "trace_id":"seed-08-dash","agent_name":"data-analyst","status":"ok",
  "task":"Generate weekly KPI dashboard for engineering team",
  "start_time":"'"$TODAY"'T09:35:00Z","end_time":"'"$TODAY"'T09:35:14Z",
  "duration_ms":14100,"total_tokens":11200,"total_cost_usd":0.0048,
  "local_tokens":4100,"cloud_tokens":7100,"model_calls_count":3,"tool_calls_count":2,
  "spans":[
    {"span_id":"s08-a","trace_id":"seed-08-dash","name":"data-analyst","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:35:00Z","end_time":"'"$TODAY"'T09:35:14Z","duration_ms":14100},
    {"span_id":"s08-t1","trace_id":"seed-08-dash","parent_span_id":"s08-a","name":"fetch_metrics","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:35:01Z","end_time":"'"$TODAY"'T09:35:03Z","duration_ms":1900,"tool_name":"fetch_metrics"},
    {"span_id":"s08-m1","trace_id":"seed-08-dash","parent_span_id":"s08-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:35:03Z","end_time":"'"$TODAY"'T09:35:05Z","duration_ms":2100,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":2800,"completion_tokens":350,"model_cost_usd":0.0},
    {"span_id":"s08-t2","trace_id":"seed-08-dash","parent_span_id":"s08-a","name":"render_dashboard","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:35:05Z","end_time":"'"$TODAY"'T09:35:08Z","duration_ms":2300,"tool_name":"render_dashboard"},
    {"span_id":"s08-m2","trace_id":"seed-08-dash","parent_span_id":"s08-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:35:08Z","end_time":"'"$TODAY"'T09:35:09Z","duration_ms":1100,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":3800,"completion_tokens":420,"model_cost_usd":0.000649},
    {"span_id":"s08-m3","trace_id":"seed-08-dash","parent_span_id":"s08-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:35:09Z","end_time":"'"$TODAY"'T09:35:11Z","duration_ms":1300,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":4100,"completion_tokens":500,"model_cost_usd":0.000714}
  ]
}'

send_trace '{
  "trace_id":"seed-09-deps","agent_name":"code-reviewer","status":"ok",
  "task":"Review PR #150: update dependency versions and fix security warnings",
  "start_time":"'"$TODAY"'T09:40:00Z","end_time":"'"$TODAY"'T09:40:11Z",
  "duration_ms":11000,"total_tokens":7600,"total_cost_usd":0.0028,
  "local_tokens":3800,"cloud_tokens":3800,"model_calls_count":2,"tool_calls_count":2,
  "spans":[
    {"span_id":"s09-a","trace_id":"seed-09-deps","name":"code-reviewer","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:40:00Z","end_time":"'"$TODAY"'T09:40:11Z","duration_ms":11000},
    {"span_id":"s09-t1","trace_id":"seed-09-deps","parent_span_id":"s09-a","name":"scan_vulnerabilities","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:40:01Z","end_time":"'"$TODAY"'T09:40:03Z","duration_ms":2200,"tool_name":"scan_vulnerabilities"},
    {"span_id":"s09-m1","trace_id":"seed-09-deps","parent_span_id":"s09-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:40:03Z","end_time":"'"$TODAY"'T09:40:05Z","duration_ms":2000,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":2900,"completion_tokens":350,"model_cost_usd":0.0},
    {"span_id":"s09-m2","trace_id":"seed-09-deps","parent_span_id":"s09-a","name":"deepseek-v4","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:40:05Z","end_time":"'"$TODAY"'T09:40:07Z","duration_ms":900,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":3000,"completion_tokens":350,"model_cost_usd":0.000518}
  ]
}'

send_trace '{
  "trace_id":"seed-10-ret","agent_name":"customer-support","status":"ok",
  "task":"Process return request RET-300 — customer changed mind within 14 days",
  "start_time":"'"$TODAY"'T09:45:00Z","end_time":"'"$TODAY"'T09:45:08Z",
  "duration_ms":8100,"total_tokens":3900,"total_cost_usd":0.0,
  "local_tokens":3900,"cloud_tokens":0,"model_calls_count":2,"tool_calls_count":1,
  "spans":[
    {"span_id":"s10-a","trace_id":"seed-10-ret","name":"customer-support","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:45:00Z","end_time":"'"$TODAY"'T09:45:08Z","duration_ms":8100},
    {"span_id":"s10-m1","trace_id":"seed-10-ret","parent_span_id":"s10-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:45:01Z","end_time":"'"$TODAY"'T09:45:03Z","duration_ms":1900,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":1600,"completion_tokens":350,"model_cost_usd":0.0},
    {"span_id":"s10-t1","trace_id":"seed-10-ret","parent_span_id":"s10-a","name":"process_return","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:45:03Z","end_time":"'"$TODAY"'T09:45:04Z","duration_ms":700,"tool_name":"process_return"},
    {"span_id":"s10-m2","trace_id":"seed-10-ret","parent_span_id":"s10-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:45:04Z","end_time":"'"$TODAY"'T09:45:06Z","duration_ms":1600,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":1400,"completion_tokens":550,"model_cost_usd":0.0}
  ]
}'

send_trace '{
  "trace_id":"seed-11-testfail","agent_name":"code-reviewer","status":"error",
  "task":"Review PR #401: add real-time notification system",
  "start_time":"'"$TODAY"'T09:50:00Z","end_time":"'"$TODAY"'T09:50:08Z",
  "duration_ms":7800,"total_tokens":5100,"total_cost_usd":0.0019,
  "local_tokens":2100,"cloud_tokens":3000,"model_calls_count":2,"tool_calls_count":1,
  "error_message":"Tests failing: 3/14 integration tests failed after merge",
  "spans":[
    {"span_id":"s11-a","trace_id":"seed-11-testfail","name":"code-reviewer","kind":"agent","status":"error","start_time":"'"$TODAY"'T09:50:00Z","end_time":"'"$TODAY"'T09:50:08Z","duration_ms":7800},
    {"span_id":"s11-t1","trace_id":"seed-11-testfail","parent_span_id":"s11-a","name":"fetch_diff","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:50:01Z","end_time":"'"$TODAY"'T09:50:02Z","duration_ms":900,"tool_name":"fetch_diff"},
    {"span_id":"s11-m1","trace_id":"seed-11-testfail","parent_span_id":"s11-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:50:02Z","end_time":"'"$TODAY"'T09:50:04Z","duration_ms":1600,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":2100,"completion_tokens":380,"model_cost_usd":0.0},
    {"span_id":"s11-m2","trace_id":"seed-11-testfail","parent_span_id":"s11-a","name":"deepseek-v4","kind":"model_call","status":"error","start_time":"'"$TODAY"'T09:50:04Z","end_time":"'"$TODAY"'T09:50:07Z","duration_ms":2800,"model_name":"accounts/fireworks/models/deepseek-v4-flash","model_provider":"fireworks","prompt_tokens":2600,"completion_tokens":340,"model_cost_usd":0.000459,"error_message":"Generated code has race condition in notification dispatch"}
  ]
}'

send_trace '{
  "trace_id":"seed-12-research","agent_name":"research-agent","status":"ok",
  "task":"Compare local LLM inference costs on AMD GPUs vs cloud APIs over 3 years",
  "start_time":"'"$TODAY"'T09:55:00Z","end_time":"'"$TODAY"'T09:55:07Z",
  "duration_ms":7000,"total_tokens":2800,"total_cost_usd":0.0,
  "local_tokens":2800,"cloud_tokens":0,"model_calls_count":2,"tool_calls_count":1,
  "spans":[
    {"span_id":"s12-a","trace_id":"seed-12-research","name":"research-agent","kind":"agent","status":"ok","start_time":"'"$TODAY"'T09:55:00Z","end_time":"'"$TODAY"'T09:55:07Z","duration_ms":7000},
    {"span_id":"s12-r1","trace_id":"seed-12-research","parent_span_id":"s12-a","name":"classify_task","kind":"reason","status":"ok","start_time":"'"$TODAY"'T09:55:01Z","end_time":"'"$TODAY"'T09:55:02Z","duration_ms":1100},
    {"span_id":"s12-t1","trace_id":"seed-12-research","parent_span_id":"s12-a","name":"web_search","kind":"tool_call","status":"ok","start_time":"'"$TODAY"'T09:55:02Z","end_time":"'"$TODAY"'T09:55:03Z","duration_ms":800,"tool_name":"web_search"},
    {"span_id":"s12-m1","trace_id":"seed-12-research","parent_span_id":"s12-a","name":"gemma3:27b","kind":"model_call","status":"ok","start_time":"'"$TODAY"'T09:55:03Z","end_time":"'"$TODAY"'T09:55:06Z","duration_ms":2600,"model_name":"gemma3:27b","model_provider":"local","prompt_tokens":2100,"completion_tokens":700,"model_cost_usd":0.0}
  ]
}'

echo ""
echo "✅ 12 traces seeded — narrative arc: success → cost → error → safety → quality"
echo "   Traces appear at http://localhost:3000"
echo "   Story beats: success ($0.00 local) → multi-model → TCO calc → ORD-9999 error → guardrail → drift"
echo ""
echo "   Local tokens:  free (AMD hardware)"
echo "   Cloud tokens:  Fireworks AI (DeepSeek V4 Flash)"
echo "   Mix:           ~55% local / 45% cloud — shows FinOps savings story"
echo "   Statuses:      8 ok, 2 error, 1 drift — realistic production mix"
