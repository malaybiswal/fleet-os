# Fleet Operating System — Design Document

## 1. Overview

The Fleet Operating System (Fleet OS) is an internal trucking operations intelligence dashboard. It ingests simulated trucking events, stores them in PostgreSQL via a FastAPI backend, calculates KPIs, and presents them through a React/Next.js frontend. The MVP is scoped to the **Dwell-Time Analytics** module using synthetic data only — no real truck integrations.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐  │
│  │  Next.js     │────▶│  FastAPI     │────▶│  PostgreSQL    │  │
│  │  Dashboard   │     │  Backend     │     │  Database      │  │
│  │  :3000       │     │  :8000       │     │  :5432         │  │
│  └──────────────┘     └──────────────┘     └────────────────┘  │
│                              │                                  │
│                       ┌──────────────┐                          │
│                       │  Simulator   │                          │
│                       │  (seed CLI)  │                          │
│                       └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Architectural Principles

- **Stateless API** — no session state stored in the API process between requests.
- **Layered backend** — Routes → Services → Repositories → Database. No raw SQL in route handlers.
- **Frontend decoupled** — consumes data exclusively via REST API; no direct DB access.
- **Type safety** — Python type hints + Pydantic models on the backend; TypeScript strict mode on the frontend.
- **Configuration via environment** — all runtime config loaded from environment variables; no hardcoded values.

---

## 3. Directory Structure

### 3.1 Repository Layout

```
fleet-os/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                    # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── main.py                 # FastAPI app entry point
│       ├── config.py               # Settings loaded from env vars
│       ├── database.py             # SQLAlchemy engine + session
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── truck.py
│       │   ├── driver.py
│       │   ├── load.py
│       │   ├── dwell_event.py
│       │   ├── telemetry_event.py
│       │   └── alert.py
│       ├── schemas/                # Pydantic request/response models
│       │   ├── truck.py
│       │   ├── driver.py
│       │   ├── load.py
│       │   ├── dwell_event.py
│       │   ├── telemetry_event.py
│       │   ├── alert.py
│       │   └── dashboard.py
│       ├── repositories/           # Data access layer
│       │   ├── base.py
│       │   ├── truck_repository.py
│       │   ├── load_repository.py
│       │   ├── telemetry_repository.py
│       │   ├── dwell_repository.py
│       │   └── alert_repository.py
│       ├── services/               # Business logic + KPI calculations
│       │   ├── truck_service.py
│       │   ├── load_service.py
│       │   ├── dwell_service.py
│       │   ├── telemetry_service.py
│       │   ├── alert_service.py
│       │   └── dashboard_service.py
│       └── routers/                # FastAPI route handlers
│           ├── health.py
│           ├── trucks.py
│           ├── loads.py
│           ├── dwell.py
│           ├── telemetry.py
│           ├── alerts.py
│           └── dashboard.py
│
├── simulator/
│   ├── seed.py                     # CLI entry point
│   ├── generators/
│   │   ├── trucks.py
│   │   ├── drivers.py
│   │   ├── loads.py
│   │   ├── dwell_events.py
│   │   ├── telemetry_events.py
│   │   └── alerts.py
│   └── config.py                   # Simulator config / defaults
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    └── src/
        ├── app/                    # Next.js App Router
        │   ├── layout.tsx
        │   ├── page.tsx            # Redirects to /dashboard
        │   ├── dashboard/page.tsx
        │   ├── dwell/page.tsx
        │   ├── trucks/page.tsx
        │   ├── loads/page.tsx
        │   └── alerts/page.tsx
        ├── components/
        │   ├── layout/
        │   │   ├── Sidebar.tsx
        │   │   └── Topbar.tsx
        │   ├── cards/
        │   │   └── KpiCard.tsx
        │   ├── charts/
        │   │   ├── DwellBarChart.tsx
        │   │   ├── BrokerBarChart.tsx
        │   │   └── DetentionChart.tsx
        │   ├── tables/
        │   │   ├── FacilityScorecard.tsx
        │   │   ├── LoadsTable.tsx
        │   │   ├── TrucksTable.tsx
        │   │   └── AlertsTable.tsx
        │   └── ui/
        │       ├── StatusBadge.tsx
        │       ├── SeverityBadge.tsx
        │       ├── ErrorMessage.tsx
        │       └── LoadingSpinner.tsx
        ├── lib/
        │   ├── api.ts              # Typed API client (fetch wrappers)
        │   └── utils.ts
        └── types/
            └── index.ts            # Shared TypeScript types
```

---

## 4. Database Schema

### 4.1 Entity-Relationship Overview

```
trucks ──────────────────────────────────────────────────────┐
  │                                                           │
  ├──< loads >──────── dwell_events                          │
  │      │                                                    │
  │      └── driver_id ──> drivers                            │
  │                                                           │
  ├──< telemetry_events                                       │
  └──< alerts ───────────────────────────────────────────────┘
```

### 4.2 Table Definitions

#### `trucks`
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| truck_id | VARCHAR(50) | UNIQUE, NOT NULL |
| status | VARCHAR(20) | NOT NULL (active / idle / maintenance) |
| current_location | VARCHAR(200) | Human-readable location string |
| current_lat | NUMERIC(9,6) | Most recent GPS latitude |
| current_lon | NUMERIC(9,6) | Most recent GPS longitude |
| last_seen_at | TIMESTAMPTZ | UTC timestamp of most recent telemetry event |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

> `current_lat`, `current_lon`, and `last_seen_at` are updated atomically whenever a telemetry event is ingested for that truck, keeping the `trucks` table as a live "last known position" store.

#### `drivers`
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| driver_id | VARCHAR(50) | UNIQUE, NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| status | VARCHAR(20) | NOT NULL (available / on_load / off_duty) |

#### `loads`
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| load_id | VARCHAR(50) | UNIQUE, NOT NULL |
| truck_id | VARCHAR(50) | FK → trucks.truck_id |
| driver_id | VARCHAR(50) | FK → drivers.driver_id |
| broker_name | VARCHAR(100) | |
| origin | VARCHAR(200) | |
| destination | VARCHAR(200) | |
| revenue | NUMERIC(10,2) | |
| miles | NUMERIC(10,2) | |
| deadhead_miles | NUMERIC(10,2) | |
| fuel_cost | NUMERIC(10,2) | |
| maintenance_reserve | NUMERIC(10,2) | |
| driver_cost | NUMERIC(10,2) | |
| tolls | NUMERIC(10,2) | |
| pickup_time | TIMESTAMPTZ | |
| delivery_time | TIMESTAMPTZ | |
| status | VARCHAR(20) | (in_transit / delivered / cancelled) |

#### `dwell_events`
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| load_id | VARCHAR(50) | FK → loads.load_id |
| facility_name | VARCHAR(200) | |
| broker_name | VARCHAR(100) | |
| appointment_time | TIMESTAMPTZ | |
| arrival_time | TIMESTAMPTZ | |
| loading_start | TIMESTAMPTZ | |
| loading_end | TIMESTAMPTZ | |
| departure_time | TIMESTAMPTZ | |
| detention_pay | NUMERIC(10,2) | |
| driver_notes | TEXT | |

#### `telemetry_events`
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| truck_id | VARCHAR(50) | FK → trucks.truck_id |
| timestamp | TIMESTAMPTZ | NOT NULL |
| speed | NUMERIC(5,2) | 0–80 mph |
| rpm | INTEGER | |
| engine_temp | NUMERIC(5,2) | 150–250 °F |
| fuel_level | NUMERIC(5,2) | 0–100 % |
| gps_lat | NUMERIC(9,6) | |
| gps_lon | NUMERIC(9,6) | |
| idle_minutes | INTEGER | |
| reefer_temp | NUMERIC(5,2) | |
| load_weight | NUMERIC(10,2) | |

#### `alerts`
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| truck_id | VARCHAR(50) | FK → trucks.truck_id |
| severity | VARCHAR(10) | low / medium / high |
| alert_type | VARCHAR(50) | high_dwell / low_fuel / reefer_temp_deviation / engine_overheat |
| message | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| resolved | BOOLEAN | DEFAULT false |

### 4.3 Indexes

| Index | Columns | Purpose |
|---|---|---|
| idx_telemetry_truck_time | telemetry_events(truck_id, timestamp) | Per-truck time-series queries |
| idx_dwell_arrival | dwell_events(arrival_time) | Date-range filtering |
| idx_loads_pickup | loads(pickup_time) | Date-range filtering |
| idx_alerts_date_resolved | alerts(created_at, resolved) | Filtered alert queries |

---

## 5. Backend Design

### 5.1 Configuration (`app/config.py`)

All configuration loaded via `pydantic-settings` from environment variables:

| Variable | Default | Description |
|---|---|---|
| DATABASE_URL | — | PostgreSQL connection string |
| API_PORT | 8000 | API listening port |
| FRONTEND_URL | http://localhost:3000 | CORS allowed origin |
| LOG_LEVEL | info | Logging level |

### 5.2 Layered Architecture

```
Request → Router → Service → Repository → Database
                ↘ Alert_Service (side-effect on ingest)
```

- **Routers** — validate HTTP request/response via Pydantic schemas. No business logic, no SQL.
- **Services** — contain all KPI calculations, business rules, and orchestration. Call repository methods only.
- **Repositories** — encapsulate all SQL/ORM queries. One class per domain entity.

### 5.3 Repository Classes

| Class | Domain | Key Methods |
|---|---|---|
| `TruckRepository` | trucks | `get_all()`, `get_by_truck_id()`, `get_active_count()`, `update_position(truck_id, lat, lon, last_seen_at)` |
| `LoadRepository` | loads | `get_all()`, `get_by_id()`, `get_by_date_range()`, `get_delivered_totals()` |
| `TelemetryRepository` | telemetry_events | `insert()`, `get_by_truck_id()` |
| `DwellRepository` | dwell_events | `insert()`, `get_all()`, `get_facility_scorecard()`, `get_broker_scorecard()` |
| `AlertRepository` | alerts | `get_all()`, `get_by_id()`, `create()`, `resolve()`, `exists_unresolved()` |

### 5.4 Service Classes

#### `DwellService`

KPI calculations:
- `dwell_time = departure_time - arrival_time` (hours)
- `loading_delay = loading_start - appointment_time` (hours)
- `facility_score = max(0, 100 - avg_dwell_hours * 10)`

Alert trigger: if `dwell_time > 4 hours` → create `high_dwell` alert (severity: medium).

#### `AnalyticsService` / `LoadService`

KPI calculations:
- `revenue_per_mile = revenue / miles`
- `deadhead_percentage = (deadhead_miles / miles) * 100`
- `net_profit = revenue - (fuel_cost + maintenance_reserve + driver_cost + tolls)`

#### `AlertService`

Telemetry-triggered alert rules:
| Condition | Alert Type | Severity |
|---|---|---|
| `fuel_level < 15%` | `low_fuel` | medium |
| `engine_temp > 230°F` | `engine_overheat` | high |
| `reefer_temp` outside 34–38°F | `reefer_temp_deviation` | high |
| `dwell_time > 4 hours` | `high_dwell` | medium |

Deduplication: before creating any alert, `AlertService` calls `AlertRepository.exists_unresolved(truck_id, alert_type)`. If an unresolved alert of the same `alert_type` already exists for the same `truck_id`, no new alert is created. This prevents alert storms from repeated telemetry events crossing the same threshold.

Telemetry side-effect: after storing a telemetry event, `TelemetryService` calls `TruckRepository.update_position(truck_id, gps_lat, gps_lon, timestamp)` to keep `current_lat`, `current_lon`, and `last_seen_at` current on the truck record.

#### `DashboardService`

Aggregates all top-level KPIs in a single method:
- `active_trucks` — count of trucks where `status = 'active'`
- `avg_dwell_hours` — mean dwell time across all dwell events
- `total_revenue` — sum of revenue across delivered loads
- `avg_revenue_per_mile` — mean RPM across delivered loads
- `deadhead_percentage` — total deadhead miles / total miles * 100 (delivered loads)
- `open_alerts` — count of alerts where `resolved = false`
- `open_loads` — count of loads where `status NOT IN ('delivered', 'cancelled')`
- `fuel_cost_per_mile` — total fuel cost / total miles (delivered loads)

### 5.5 API Endpoints

#### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | DB connectivity + uptime check |

#### Trucks
| Method | Path | Description |
|---|---|---|
| GET | `/api/trucks` | List all trucks with status + location |

#### Telemetry
| Method | Path | Description |
|---|---|---|
| POST | `/api/telemetry` | Ingest telemetry event |
| GET | `/api/telemetry/{truck_id}` | Get telemetry for truck (paginated, desc) |

#### Dwell
| Method | Path | Description |
|---|---|---|
| POST | `/api/dwell` | Record a dwell event |
| GET | `/api/dwell/events` | List all dwell events (paginated) |
| GET | `/api/dwell/facility-scorecard` | Facility scorecard (filterable by date) |
| GET | `/api/dwell/broker-scorecard` | Broker scorecard |

#### Loads
| Method | Path | Description |
|---|---|---|
| POST | `/api/loads` | Create a load |
| GET | `/api/loads` | List loads (paginated, filterable by date) |
| GET | `/api/loads/{load_id}/profitability` | Per-load profitability report |

#### Alerts
| Method | Path | Description |
|---|---|---|
| GET | `/api/alerts` | List alerts (paginated, filterable by resolved) |
| PATCH | `/api/alerts/{alert_id}/resolve` | Mark alert as resolved |

#### Dashboard
| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard/summary` | All top-level KPIs (filterable by date) |

#### Docs
| Method | Path | Description |
|---|---|---|
| GET | `/docs` | Swagger / OpenAPI UI |

### 5.6 Pagination

All list endpoints support `?limit=100&offset=0` query parameters. Default and maximum page size is 100 records.

### 5.7 Error Responses

All 4xx and 5xx errors return structured JSON:
```json
{
  "error": "Human-readable message describing what went wrong"
}
```

### 5.8 Request Logging

Every API request log entry includes:
- `request_id` — UUID generated per request (via middleware)
- `timestamp` — UTC ISO 8601
- `method`, `path`, `status_code`, `duration_ms`

---

## 6. Simulator Design

### 6.1 CLI Interface

```bash
python simulator/seed.py \
  --trucks 10 \
  --drivers 10 \
  --loads 100 \
  --dwell-events 200 \
  --telemetry-events 5000 \
  --alerts 50 \
  --start-date 2024-11-01 \
  --end-date 2024-11-30 \
  --alert-frequency 0.1 \
  --seed 42          # optional: deterministic RNG
```

### 6.2 Generation Rules

| Entity | Constraints |
|---|---|
| Trucks | status: active / idle / maintenance |
| Drivers | status: available / on_load / off_duty |
| Loads | revenue $500–$5000, miles 50–2000, deadhead 0–500 |
| Dwell Events | arrival < loading_start < loading_end < departure |
| Telemetry | speed 0–80 mph, fuel 0–100%, engine_temp 150–250°F |
| Alerts | severity: low / medium / high; types: high_dwell, low_fuel, reefer_temp_deviation, engine_overheat |

### 6.3 Idempotency

When the seed script is run a second time, it clears all existing synthetic data before re-inserting (truncate in FK-safe order), preventing duplicate records.

---

## 7. Frontend Design

### 7.1 Technology Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **HTTP client**: fetch with typed wrappers in `lib/api.ts`

### 7.2 Pages and Routes

| Route | Component | Data Source |
|---|---|---|
| `/dashboard` | Dashboard landing | `GET /api/dashboard/summary` |
| `/dwell` | Dwell analytics | `GET /api/dwell/facility-scorecard`, `GET /api/dwell/broker-scorecard` |
| `/trucks` | Truck status | `GET /api/trucks` |
| `/loads` | Load profitability | `GET /api/loads`, `GET /api/loads/{id}/profitability` |
| `/alerts` | Alerts management | `GET /api/alerts`, `PATCH /api/alerts/{id}/resolve` |

### 7.3 Page Designs

#### `/dashboard` — Landing Page

Seven KPI cards arranged in a responsive grid:

| Card | Value | Unit |
|---|---|---|
| Active Trucks | count | trucks |
| Open Loads | count | loads |
| Avg Dwell Time | decimal | hours |
| Revenue per Mile | currency | $/mile |
| Deadhead % | percentage | % |
| Fuel Cost per Mile | currency | $/mile |
| Open Alerts | count | alerts |

Behavior:
- Fetches `GET /api/dashboard/summary` on mount.
- Shows loading spinner while fetching.
- Shows inline error message if API fails.
- Navigation sidebar links to all pages.

#### `/dwell` — Dwell Analytics

- **Facility Scorecard Table** — columns: Facility, Broker, Avg Wait Time, Detention Pay, Visits, Score. Sortable by Score.
- **Top 10 Worst Facilities Bar Chart** — x-axis: facility name, y-axis: avg dwell hours. Descending order.
- **Avg Dwell by Broker Bar Chart** — grouped by broker name.
- **Detention Pay Chart** — side-by-side bars: recovered vs lost detention pay per facility.

#### `/trucks` — Truck Status

Table with color-coded status badges:
- 🟢 Green — `active`
- 🟡 Yellow — `idle`
- 🔴 Red — `maintenance`

Columns: Truck ID, Status, Current Location, Last Seen At. The `current_lat` and `current_lon` fields are stored and available for future map integration but not rendered in the MVP table view.

#### `/loads` — Load Profitability

- Table: Load ID, Broker, Origin, Destination, Revenue, Miles, RPM, Deadhead %, Status.
- Clicking a row opens a detail panel (slide-over or modal) showing the full profitability report from `GET /api/loads/{load_id}/profitability`.

#### `/alerts` — Alerts

- Table: Truck ID, Severity, Type, Message, Created At, Status.
- Color-coded severity badges: 🔴 high, 🟠 medium, 🟡 low.
- Filter toggle: All / Open / Resolved.
- "Resolve" button on unresolved rows — fires `PATCH /api/alerts/{id}/resolve`, updates row in-place without full page reload.

### 7.4 Shared Components

| Component | Purpose |
|---|---|
| `KpiCard` | Summary metric card with label, value, optional trend |
| `StatusBadge` | Color-coded truck status pill |
| `SeverityBadge` | Color-coded alert severity pill |
| `ErrorMessage` | User-visible API error display |
| `LoadingSpinner` | Loading state indicator |
| `Sidebar` | Navigation links to all pages |

### 7.5 API Client (`lib/api.ts`)

Typed fetch wrappers for every endpoint. All functions are async, return typed response objects, and throw on non-2xx responses. Base URL configured via `NEXT_PUBLIC_API_URL` environment variable.

---

## 8. Infrastructure

### 8.1 Docker Compose Services

```yaml
services:
  db:         # PostgreSQL 15, named volume for persistence
  api:        # FastAPI, depends_on db with healthcheck, port 8000
  frontend:   # Next.js, depends_on api, port 3000
```

### 8.2 Environment Variables (`.env.example`)

```env
# Database
DATABASE_URL=postgresql://fleetuser:fleetpass@db:5432/fleetdb
POSTGRES_USER=fleetuser
POSTGRES_PASSWORD=fleetpass
POSTGRES_DB=fleetdb

# API
API_PORT=8000
LOG_LEVEL=info

# CORS
FRONTEND_URL=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 8.3 API Startup Retry

On startup the API retries the database connection with exponential backoff up to a 30-second timeout before failing.

### 8.4 Database Migrations

Managed via **Alembic**. Initial migration `001_initial_schema.py` creates all tables, foreign keys, and indexes. Running migrations against an existing database applies only missing changes — no data loss.

---

## 9. MVP Phase Plan

### Phase 1 (Core — ship first)

| Area | Deliverables |
|---|---|
| Infrastructure | docker-compose, .env, README, health endpoint |
| Database | Full schema + Alembic migration |
| Simulator | Seed script generating all entity types |
| Backend | Dashboard summary API, Dwell API, Alert API, Truck list |
| Frontend | `/dashboard`, `/dwell`, `/alerts`, navigation |

### Phase 2 (Extend — ship second)

| Area | Deliverables |
|---|---|
| Backend | Load profitability API, Telemetry detail API |
| Frontend | `/loads`, `/trucks`, load detail modal, telemetry views |

Phase 1 must be fully functional as a standalone operational tool for the dwell analytics and alerts use cases before Phase 2 begins.

---

## 10. Non-Functional Design Decisions

| Requirement | Design Decision |
|---|---|
| `/api/dashboard/summary` < 500ms | Pre-aggregation queries with indexed columns; no N+1 queries |
| 100k telemetry events — no degradation | Composite index on `(truck_id, timestamp)`; paginated API responses |
| Dashboard renders < 2s locally | SSR for initial page load in Next.js; lightweight chart library (Recharts) |
| Structured error JSON | FastAPI exception handler middleware returning `{"error": "..."}` |
| Request tracing | UUID middleware injecting `request_id` into every log entry |
| Zero manual setup | All services, migrations, and seed steps documented in `README.md`; runnable via single `docker-compose up` |

---

## 11. Out of Scope (MVP)

- Real ELD / GPS / broker API integration
- User authentication and authorization (JWT hooks stubbed in route definitions for future use)
- Payment or invoicing systems
- Mobile applications
- ML prediction models or route optimization
- Multi-tenant / SaaS deployment