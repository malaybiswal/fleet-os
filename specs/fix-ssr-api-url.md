# Fix: SSR API URL Resolution in Docker

## Problem

The Next.js homepage threw a server-side exception (digest `3339239339`) on every load:

```
TypeError: fetch failed
cause: AggregateError [ECONNREFUSED]
```

The root cause: Next.js server-side renders the homepage by fetching the API at build/request time. Inside the Docker container, the frontend was calling `http://localhost:8000`, but `localhost` inside the container refers to the frontend container itself — not the API service. The API is only reachable via the Docker Compose service name `http://api:8000`.

The `NEXT_PUBLIC_API_URL=http://localhost:8000` env var is correct for the browser (client-side), but wrong for server-side rendering.

## Fix

Added a separate server-only env var `API_URL=http://api:8000` for use during SSR, while keeping `NEXT_PUBLIC_API_URL` for browser-side fetches.

### Files Changed

**`docker-compose.yml`** — added `API_URL` to the frontend service environment:
```yaml
environment:
  NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000}
  API_URL: http://api:8000
```

**`frontend/src/lib/api.ts`** — prefer `API_URL` over `NEXT_PUBLIC_API_URL` at runtime:
```ts
const API_BASE_URL =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

`API_URL` is not prefixed with `NEXT_PUBLIC_`, so Next.js only exposes it server-side. Browser code never sees it and falls through to `NEXT_PUBLIC_API_URL` as expected.

**`frontend/src/app/dwell/page.tsx`** — removed hardcoded `http://localhost:8000` in client-side fetches, replaced with `process.env.NEXT_PUBLIC_API_URL`.

## Behaviour After Fix

| Context | URL used |
|---|---|
| SSR (inside Docker container) | `http://api:8000` via `API_URL` |
| Browser (client-side fetches) | `http://localhost:8000` via `NEXT_PUBLIC_API_URL` |
| Local dev outside Docker | `http://localhost:8000` fallback |
