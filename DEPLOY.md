# Deployment

Argus is deployed on a self-hosted VM at `argus.perciqa.com`.

## Server

| Detail | Value |
|--------|-------|
| Host | `130.107.145.244` |
| User | `perciqa-argus` |
| Path | `/home/perciqa-argus/argus` |
| Docker | `docker compose` (29.5.3) |
| Ports | `8000:8000` (server), `3007:3000` (UI) |

## Deploy

```bash
ssh perciqa-argus@130.107.145.244
cd argus && git pull origin main && docker compose up -d --build
```

The server auto-generates a demo API key at startup if `ARGUS_API_KEY` is not set. The dashboard displays it in the sidebar for copy-paste into the SDK.

## Verify

```bash
# Server health
curl -s https://argus.perciqa.com/api/health

# API key (from VM)
curl -s localhost:8000/api/config

# UI
curl -s https://argus.perciqa.com | grep sidebar-api-key
```
