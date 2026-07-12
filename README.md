# Argus by Perciqa

> **Ship agents that don't break. Know exactly why when they do.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![AMD Hackathon](https://img.shields.io/badge/AMD-Hackathon%20Act%20II-ED1C24)](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii)
[![Built for AMD Hackathon](https://img.shields.io/badge/AMD%20Hackathon-Act%20II-orange)](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii)

Argus is an open-source agent reliability engine that gives you **trajectory tracing**, **inference FinOps**, and **eval-in-production** -- in a single tool, with zero external dependencies for local use.

---

## Why Argus?

AI agents fail silently. A customer service agent hallucinating a refund policy, a research agent fabricating a citation -- both return `200 OK`. Traditional APM tools (Datadog, New Relic) track *system health*, not *agent reasoning*.

Argus closes this gap:

| Pain Point | Argus Solution |
|---|---|
| **Silent failures** | LLM-as-judge eval on live traffic scores every agent run |
| **Opaque debugging** | Interactive trajectory viewer shows the full decision tree |
| **Cost spirals** | Per-task cost tracking with local vs. cloud split |
| **Compliance gaps** | Structured audit trails for every agent decision |

---

## Try the Live Demo

Argus is running at **https://argus.perciqa.com**. Wire your agent into it in
under a minute:

```bash
pip install git+https://github.com/perciqa/argus.git#subdirectory=packages/sdk
```

```python
import argus

argus.init(
    server_url="https://argus.perciqa.com",
    api_key="<your-key-from-sidebar>",  # get it at argus.perciqa.com
    agent_name="my-agent",
)
```

Traces appear in the dashboard in real time -- no local setup needed.

---

## Quickstart (Self-Hosted)

```bash
# 1. Copy .env.example and set your keys
cp .env.example .env
# Edit .env: set ARGUS_API_KEY and (optionally) FIREWORKS_API_KEY

# 2. Start everything
docker compose up --build

# 3. Open http://localhost:3000
```

Or instrument your own agent locally:

```python
import argus
from openai import OpenAI

argus.init(server_url="http://localhost:8000", agent_name="my-agent")
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

@argus.trace(kind="agent")
def my_agent(query: str) -> str:
    # OpenAI calls are auto-intercepted -- no extra code needed
    response = client.chat.completions.create(
        model="gemma3:27b",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content

# Every call is traced, costed, and scored automatically
my_agent("Explain quantum entanglement")
```

---

## Features

### 🔭 Trajectory Tracing
Capture the full decision tree of every agent run -- every reasoning step, tool call, and model selection -- as a replayable, structured trace. Visualize it as an interactive tree with timing, cost, and error highlighting.

### 💰 Inference FinOps
Track cost *per task*, not per GPU. See exactly how much each agent run costs, with local vs. cloud breakdowns. Local inference is automatically counted as **$0.00** -- giving you a real picture of your savings.

### 🧪 Eval-in-Production
Automatically score agent quality on every trace using **DeepSeek V4 Flash** via Fireworks AI serverless ($0.07/M tokens). Detect regressions before users do. Falls back to local Ollama when no API key is set.

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

## AMD & Fireworks Integration

Argus is built **AMD-first** by design: no CUDA dependencies, ROCm-compatible
architecture, and a FinOps layer that treats local GPU inference as $0.00.

**AMD inference** -- Local model runs (Gemma, Llama, via Ollama or AMD Developer
Cloud) are tracked automatically. The FinOps dashboard shows local vs. cloud
cost split, proving real savings from running on AMD hardware.

**Fireworks AI** powers the eval engine: every agent trace is automatically
scored by DeepSeek V4 Flash via Fireworks serverless inference
($0.07/M tokens). Set `FIREWORKS_API_KEY` in `.env` to enable it.
Falls back to local Ollama if no key is set.

---

## Tech Stack

| Layer | Technology |
|---|---|
| SDK | Python 3.12+, Pydantic v2, httpx |
| Server | FastAPI, aiosqlite, uvicorn |
| Dashboard | Next.js 16, Mantine v7, Mantine Charts |
| Eval | DeepSeek V4 Flash via Fireworks AI serverless |
| Infrastructure | Docker, Docker Compose |

---

## Development Setup

```bash
# Clone
git clone https://github.com/perciqa/argus.git
cd argus

# Environment
cp .env.example .env   # set ARGUS_API_KEY and FIREWORKS_API_KEY

# Start everything (Docker)
docker compose up --build

# Or run locally:
python -m venv .venv && source .venv/bin/activate
pip install -e packages/server -e packages/sdk
uvicorn app.main:app --reload --port 8000 --app-dir packages/server &
cd packages/ui && npm install && npm run dev
```

---

## Project Structure

```
argus/
├── packages/
│   ├── sdk/          # Python SDK (argus)
│   ├── server/       # FastAPI backend + eval engine
│   └── ui/           # Next.js 16 dashboard (Mantine v7)
├── scripts/          # Demo helpers
├── docker-compose.yml
├── nginx.conf
├── .env.example
└── README.md
```

---

## Contributing

Argus is MIT-licensed and welcomes contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Built By

**Perciqa** -- Built for the [AMD Developer Hackathon Act II](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii).

> *Argus* -- from Greek mythology, the hundred-eyed giant who never slept. If you can't see everything your agent does, you can't trust it.
