# Prism Ops Console

React + TypeScript + Vite + Tailwind CSS frontend for the Prism LLM Gateway.

## Start

```bash
npm install
npm run dev
```

The Vite dev server runs on `http://localhost:5173`.

The dev proxy forwards `/v1/*` requests to the FastAPI backend at:

```text
http://127.0.0.1:8000
```

Start the Prism backend separately.

## Dashboard APIs

The console calls:

```text
GET /v1/usage
GET /v1/usage/summary
```

Both endpoints use:

```http
Authorization: Bearer <PRISM_VIRTUAL_API_KEY>
```

The dashboard is tenant-scoped because the backend resolves the authenticated
application from the virtual API key rather than accepting an arbitrary tenant
identifier from the browser.

## Current scope

The first console slice shows:

- request count and successful requests
- total cost and token usage
- cache hit rate
- cache hits and misses
- fallback requests
- average latency
- recent request records
- model/provider/cache/status/fallback details
