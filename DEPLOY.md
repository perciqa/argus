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

## Quick Setup (new VM)

```bash
ssh perciqa-argus@130.107.145.244
cd argus

# Generate a strong API key
echo "ARGUS_API_KEY=arg_$(openssl rand -hex 24)" > .env

# Add other required secrets
echo "AUTH_SECRET=$(openssl rand -base64 32)" >> .env
echo "AUTH_GITHUB_ID=..." >> .env
echo "AUTH_GITHUB_SECRET=..." >> .env

docker compose up -d --build
```

## Deploy (update)

```bash
ssh perciqa-argus@130.107.145.244
cd argus && git pull origin main && docker compose up -d --build
```

The server auto-generates a demo API key at startup if `ARGUS_API_KEY` is not set, but you must set it explicitly so the UI proxy can inject it into API requests. The dashboard displays the key in the sidebar for copy-paste into the SDK.

## Verify

```bash
# Server health (public)
curl -s https://argus.perciqa.com/api/health

# Authenticated endpoints (requires API key)
curl -s -H "X-API-Key: $ARGUS_API_KEY" http://localhost:8000/api/config
curl -s -H "X-API-Key: $ARGUS_API_KEY" http://localhost:8000/api/traces
curl -s -H "X-API-Key: $ARGUS_API_KEY" http://localhost:8000/api/finops/summary

# UI (proxied, no API key needed in browser)
curl -s https://argus.perciqa.com | grep sidebar-api-key
```
