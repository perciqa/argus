# Argus by Perciqa

> **Ship agents that don't break. Know exactly why when they do.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![AMD ROCm](https://img.shields.io/badge/AMD-ROCm%20Native-ED1C24)](https://rocm.amd.com)
[![Built for AMD Hackathon](https://img.shields.io/badge/AMD%20Hackathon-Act%20II-orange)](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii)

Argus is an open-source agent reliability engine that gives you **trajectory tracing**, **inference FinOps**, and **eval-in-production** — in a single tool, with zero external dependencies for local use.

---

## Why Argus?

AI agents fail silently. A customer service agent hallucinating a refund policy, a research agent fabricating a citation — both return `200 OK`. Traditional APM tools (Datadog, New Relic) track *system health*, not *agent reasoning*.

Argus closes this gap:

| Pain Point | Argus Solution |
|---|---|
| **Silent failures** | LLM-as-judge eval on live traffic scores every agent run |
| **Opaque debugging** | Interactive trajectory viewer shows the full decision tree |
| **Cost spirals** | Per-task cost tracking with local vs. cloud split |
| **Compliance gaps** | Structured audit trails for every agent decision |

---

## Quickstart

```bash
# 1. Install the SDK
pip install argus-sdk

# 2. Instrument your agent
import argus

@argus.trace(name="my_agent", kind="agent")
def my_agent(query: str) -> str:
    result = search(query)
    return summarize(result)

# 3. Start the dashboard
docker compose up

# 4. Run your agent — traces appear in real-time at http://localhost:3000
my_agent("Explain quantum entanglement")
```

That's it. No config files, no account creation, no infrastructure setup.

---

## Features

### 🔭 Trajectory Tracing
Capture the full decision tree of every agent run — every reasoning step, tool call, and model selection — as a replayable, structured trace. Visualize it as an interactive tree with timing, cost, and error highlighting.

### 💰 Inference FinOps
Track cost *per task*, not per GPU. See exactly how much each agent run costs, with local vs. cloud breakdowns. Local AMD GPU inference is automatically counted as **$0.00** — giving you a real picture of your savings.

### 🧪 Eval-in-Production
Continuously score agent quality using LLM-as-judge evaluation (Gemma on AMD Developer Cloud) on live traffic. Detect regressions before users do.

---

## Architecture

```
┌─────────────────────────┐     HTTP POST      ┌──────────────────────┐
│   Your Agent Code       │  ──────────────►   │   Argus Server       │
│   @argus.trace(...)     │                    │   FastAPI + SQLite   │
│   OpenAI Interceptor    │                    │   Eval Engine        │
└─────────────────────────┘                    └──────────┬───────────┘
                                                          │ WebSocket
                                               ┌──────────▼───────────┐
                                               │   Argus Dashboard    │
                                               │   Next.js            │
                                               │   Trajectory Viewer  │
                                               │   FinOps Dashboard   │
                                               │   Eval Scoreboard    │
                                               └──────────────────────┘
```

**AMD Integration:**
- Local model inference (Gemma, Llama) runs on AMD Developer Cloud (MI300X)
- Eval judge (Gemma) runs on AMD GPU — eval costs tracked as $0.00
- Full ROCm compatibility — no CUDA dependencies

---

## Tech Stack

| Layer | Technology |
|---|---|
| SDK | Python 3.10+, Pydantic v2, httpx |
| Server | FastAPI, aiosqlite, uvicorn |
| Dashboard | Next.js 15, Recharts, Vanilla CSS |
| Eval | Gemma via AMD Developer Cloud / Fireworks AI |
| Infrastructure | Docker, Docker Compose |

---

## Development Setup

```bash
# Clone
git clone https://github.com/perciqa/argus.git
cd argus

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Start everything
docker compose up

# Or run components individually:
pip install -e packages/sdk[dev]
cd packages/server && uvicorn app.main:app --reload
cd packages/ui && npm run dev
```

---

## Project Structure

```
argus/
├── packages/
│   ├── sdk/          # pip install argus-sdk
│   ├── server/       # FastAPI backend
│   └── ui/           # Next.js dashboard
├── demo/             # Demo agent (multi-model routing)
├── data/             # SQLite database (gitignored)
├── tests/            # Integration tests
├── docker-compose.yml
├── AI_DISCLOSURE.md
└── LICENSE
```

---

## Contributing

Argus is MIT-licensed and welcomes contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Built By

**Perciqa** — Built for the [AMD Developer Hackathon Act II](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii).

> *Argus* — from Greek mythology, the hundred-eyed giant who never slept. If you can't see everything your agent does, you can't trust it.
