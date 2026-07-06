# Argus SDK

The Python SDK for **Argus by Perciqa** — the agent reliability engine.

## Install

```bash
pip install -e .
```

## Quick Start

```python
import ratioc as argus

argus.init(server_url="http://localhost:8000", agent_name="my-agent")

@argus.trace(name="my_agent", kind="agent")
def my_agent(query: str) -> str:
    return do_something(query)
```
