# Fleet Operating System

An internal trucking operations intelligence dashboard built with FastAPI, PostgreSQL, and Next.js. Uses synthetic data only — no real truck integrations.

---

## Prerequisites

| Tool | Minimum Version |
|---|---|
| Docker | 24+ |
| Docker Compose | v2 (bundled with Docker Desktop) |
| Git | any |

> Python and Node.js are **not** required on your host machine. Everything runs inside containers.

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repo-url> fleet-os
cd fleet-os
```

### 2. Create your environment file

```bash
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local development. You only need to edit `.env` if you want to change ports, credentials, or log level.

### 3. Start all services

```bash
docker compose up --build
```

This command:
- Builds the FastAPI backend image
- Builds the Next.js frontend image
- Starts PostgreSQL 15 with a persistent named volume
- Waits for the database to be healthy before starting the API
- Waits for the API to be healthy before starting the frontend

First build takes 2–4 minutes. Subsequent starts are fast.

### 4. Verify everything is running

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

### 5. Seed the database with synthetic data

In a separate terminal, run the simulator to populate 30 days of fake trucking data:

```bash
docker compose exec api python -m simulator.seed
```

With custom parameters:

```bash
docker compose exec api python -m simulator.seed \
  --trucks 20 \
  --loads 200 \
  --dwell-events 400 \
  --telemetry-events 10000 \
  --start-date 2024-10-01 \
  --end-date 2024-10-31 \
  --seed 42
```

Re-running the seed script clears all existing data before inserting fresh records.

---

## Stopping and Restarting

```bash
# Stop all containers (data is preserved in the Docker volume)
docker compose down

# Stop and remove all data (full reset)
docker compose down -v

# Restart without rebuilding images
docker compose up
```

---

## Running Database Migrations

Migrations are run automatically when the API container starts. To run them manually:

```bash
docker compose exec api alembic upgrade head
```

---

## Project Structure

```
fleet-os/
├── docker-compose.yml        # Orchestrates all three services
├── .env.example              # Template for environment variables
├── README.md                 # This file
│
├── backend/                  # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/              # Database migrations
│   └── app/
│       ├── main.py           # App entry point
│       ├── config.py         # Settings from env vars
│       ├── database.py       # SQLAlchemy engine + session
│       ├── models/           # ORM models
│       ├── schemas/          # Pydantic request/response models
│       ├── repositories/     # Data access layer
│       ├── services/         # Business logic + KPI calculations
│       └── routers/          # API route handlers
│
├── simulator/                # Synthetic data generator
│   ├── seed.py               # CLI entry point
│   └── generators/           # Per-entity data generators
│
└── frontend/                 # Next.js dashboard
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── app/              # Next.js App Router pages
        ├── components/       # Reusable UI components
        ├── lib/              # API client + utilities
        └── types/            # TypeScript type definitions
```

---

## Environment Variables

All configuration is loaded from environment variables. See `.env.example` for the full list with descriptions.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `fleetuser` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `fleetpass` | PostgreSQL password |
| `POSTGRES_DB` | `fleetdb` | PostgreSQL database name |
| `DATABASE_URL` | *(derived)* | Full PostgreSQL connection string |
| `API_PORT` | `8000` | Port the FastAPI server listens on |
| `LOG_LEVEL` | `info` | Logging level (`debug`/`info`/`warning`/`error`) |
| `FRONTEND_URL` | `http://localhost:3000` | Allowed CORS origin for the frontend |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL used by the browser |

---

## API Overview

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health + DB connectivity |
| GET | `/docs` | Swagger / OpenAPI UI |
| GET | `/api/dashboard/summary` | Top-level KPIs |
| GET | `/api/trucks` | All trucks with status |
| POST | `/api/telemetry` | Ingest telemetry event |
| GET | `/api/telemetry/{truck_id}` | Telemetry history for a truck |
| POST | `/api/dwell` | Record a dwell event |
| GET | `/api/dwell/events` | All dwell events |
| GET | `/api/dwell/facility-scorecard` | Facility performance scorecard |
| GET | `/api/dwell/broker-scorecard` | Broker performance scorecard |
| POST | `/api/loads` | Create a load |
| GET | `/api/loads` | All loads |
| GET | `/api/loads/{load_id}/profitability` | Per-load profitability report |
| GET | `/api/alerts` | All alerts |
| PATCH | `/api/alerts/{alert_id}/resolve` | Resolve an alert |

---

## Troubleshooting

**Port already in use**
If ports 3000 or 8000 are taken, edit `API_PORT` and/or `NEXT_PUBLIC_API_URL` in your `.env` file, then restart with `docker compose up`.

**Docker daemon not running**
Make sure Docker Desktop (or the Docker daemon) is started before running any `docker compose` commands.

**Build fails on first run**
Try `docker compose build --no-cache` to force a clean rebuild, then `docker compose up`.

**Database connection errors on startup**
The API retries the database connection for up to 30 seconds. If it still fails, run `docker compose down -v` to wipe the volume and start fresh.

---

## Development Notes

- All timestamps are stored and returned in **UTC ISO 8601** format.
- PostgreSQL data persists in the `fleet_pgdata` Docker volume across container restarts.
- The API retries the database connection for up to 30 seconds on startup.
- Alert deduplication is enforced: no duplicate open alerts for the same truck + alert type.
- The simulator supports a `--seed` flag for deterministic, reproducible datasets.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | PostgreSQL 15 |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| Infrastructure | Docker, Docker Compose |
