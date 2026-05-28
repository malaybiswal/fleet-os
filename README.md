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

### 6. Reset the deterministic demo environment

For product demos, screenshots, debugging, and onboarding, reset the database to the curated FleetOS demo scenario:

```bash
make reset-demo
```

This runs:

```bash
docker compose exec api python -m app.seed.demo_environment
```

The reset only affects rows with the demo fleet names or `DEMO-` identifiers. Non-demo rows are preserved. Demo fleet rows are reused when users are already assigned to them, so local auth mappings remain valid.

The demo environment includes:

- demo fleets, trucks, and drivers
- strategic demo loads for good load, bad load, high dwell, strong reload, bad deadhead, and weak broker scenarios
- telemetry history for live fleet map movement and operational statuses
- unresolved and resolved alerts for alerting demos
- dwell events with seeded facility names and broker names

Facilities and brokers are represented by `facility_name` and `broker_name` values on dwell events and loads. TASK-032N does not add first-class facility or broker tables; those belong to later facility and broker intelligence tasks.

Preview the reset without writing data:

```bash
make reset-demo-dry-run
```

Pass supported CLI options through `DEMO_ARGS`:

```bash
make reset-demo DEMO_ARGS="--seed 32032 --base-date 2026-06-01T14:00:00Z"
```

The direct backend command still supports:

| Option | Description |
|---|---|
| `--dry-run` | Print rows that would be deleted and created without writing data |
| `--seed <number>` | Use a deterministic seed for generated demo values |
| `--base-date <timestamp>` | Set the UTC demo base date/time, for example `2026-06-01T14:00:00Z` |

### 7. Import FMCSA carrier census data

Use the carrier ingestion CLI to import FMCSA Company Census carriers into the carrier intelligence tables:

```bash
docker compose exec api python -m app.jobs.carrier_ingestion
```

For local testing, start with a small capped run:

```bash
docker compose exec api python -m app.jobs.carrier_ingestion \
  --record-cap 5 \
  --state TX \
  --authority-status active \
  --page-size 5 \
  --log-level info
```

Successful runs print a summary like:

```text
Carrier ingestion complete: fetched=5 upserted=5 skipped=0 batches_committed=1
```

Supported options:

| Option | Description |
|---|---|
| `--record-cap <number>` | Stop after processing this many records |
| `--state <XX>` | Filter by two-letter physical state, for example `TX` |
| `--authority-status <active\|inactive\|pending>` | Filter by FMCSA authority status |
| `--min-power-units <number>` | Import carriers with at least this many power units |
| `--max-power-units <number>` | Import carriers with no more than this many power units |
| `--page-size <number>` | FMCSA API page size and database commit batch size |
| `--log-level <debug\|info\|warning\|error>` | CLI logging verbosity |

FMCSA returns the current Company Census baseline, not historical snapshots. The CLI intentionally does not expose a snapshot-date option.

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

## Testing

### Run Backend Tests

Run a single API test file:


docker compose exec api pytest tests/routers/test_trucks_api.py -v

### Run the complete backend test suite:
docker compose exec api pytest

### Run carrier ingestion CLI tests:
docker compose exec api pytest tests/jobs/test_carrier_ingestion.py

### Run demo environment seed tests:
docker compose exec api pytest tests/seed -q

Integration tests create temporary test fleets and related test data for multi-tenant validation.
Test data is automatically cleaned up after successful test execution.
If a test fails unexpectedly, temporary rows may remain in the database. Verify and manually remove leftover TEST-* records if needed.

### Example cleanup commands:

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from alerts where truck_id like 'TEST-%';"

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from telemetry_events where truck_id like 'TEST-%';"

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from dwell_events where load_id like 'TEST-%';"

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from loads where load_id like 'TEST-%';"

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from trucks where truck_id like 'TEST-%';"

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from drivers where driver_id like 'TEST-%';"

docker compose exec db psql -U fleetuser -d fleetdb -c "delete from fleets where name like 'Test Fleet%';"

### Run frontend tests using:

npm test
