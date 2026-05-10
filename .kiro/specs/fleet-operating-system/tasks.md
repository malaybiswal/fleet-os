# Fleet Operating System — Task List

## Phase 1 Tasks

---

### TASK-001: Project Scaffolding and Docker Compose Setup

**Priority**: P0 — Must complete first; all other tasks depend on this.

**Description**
Create the root repository structure, Docker Compose configuration, and environment variable setup so all services can be started with a single command.

**Acceptance Criteria**
- [x] Repository root contains `docker-compose.yml`, `.env.example`, and `README.md`
- [x] `docker-compose.yml` defines three services: `db` (PostgreSQL 15), `api` (FastAPI on port 8000), `frontend` (Next.js on port 3000)
- [x] PostgreSQL service uses a named Docker volume for data persistence
- [x] API service has a `depends_on` health check so it waits for the DB to be ready
- [x] `.env.example` documents all required variables: `DATABASE_URL`, `API_PORT`, `FRONTEND_URL`, `LOG_LEVEL`, `NEXT_PUBLIC_API_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- [x] `README.md` contains step-by-step local setup instructions
- [x] `docker-compose up` starts all three services successfully

**Files to Create**
- `docker-compose.yml`
- `.env.example`
- `README.md`

**Dependencies**: None

---

### TASK-002: Backend Project Structure and FastAPI App Init

**Priority**: P0

**Description**
Initialize the FastAPI backend with the correct directory layout, configuration loading, database connection, logging middleware, and CORS setup.

**Acceptance Criteria**
- [x] Directory structure matches design: `backend/app/{main.py, config.py, database.py, models/, schemas/, repositories/, services/, routers/}`
- [x] `config.py` loads all settings from environment variables using `pydantic-settings`
- [x] `database.py` creates SQLAlchemy engine and session factory
- [x] API retries DB connection with backoff up to 30-second timeout on startup
- [x] CORS middleware enabled; allowed origins configurable via `FRONTEND_URL` env var
- [x] Request logging middleware injects `request_id` (UUID) and `timestamp` into every log entry
- [x] All 4xx/5xx errors return `{"error": "..."}` JSON via global exception handler
- [ ] `GET /health` returns HTTP 200 with DB connectivity status and uptime
- [~] `GET /docs` serves Swagger/OpenAPI UI
- [~] `requirements.txt` includes: fastapi, uvicorn, sqlalchemy, pydantic-settings, alembic, psycopg2-binary, python-dotenv

**Files to Create**
- `backend/Dockerfile`
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/routers/health.py`

**Dependencies**: TASK-001

---

### TASK-003: Database Schema and Alembic Migration

**Priority**: P0

**Description**
Define all SQLAlchemy ORM models and create the Alembic migration that builds the full schema from scratch.

**Acceptance Criteria**
- [~] ORM models created for: `trucks`, `drivers`, `loads`, `dwell_events`, `telemetry_events`, `alerts`
- [~] All columns match the schema in the design doc (types, nullability, defaults)
- [~] `trucks` table includes `current_lat NUMERIC(9,6)`, `current_lon NUMERIC(9,6)`, and `last_seen_at TIMESTAMPTZ` columns in addition to the base columns
- [~] All foreign key constraints defined:
  - `loads.truck_id` → `trucks.truck_id`
  - `loads.driver_id` → `drivers.driver_id`
  - `dwell_events.load_id` → `loads.load_id`
  - `telemetry_events.truck_id` → `trucks.truck_id`
  - `alerts.truck_id` → `trucks.truck_id`
- [~] All indexes created:
  - Composite: `telemetry_events(truck_id, timestamp)`
  - Single: `dwell_events(arrival_time)`
  - Single: `loads(pickup_time)`
  - Composite: `alerts(created_at, resolved)`
- [~] All timestamps stored as `TIMESTAMPTZ` (UTC)
- [~] Alembic configured with `alembic.ini` and `alembic/env.py`
- [~] Migration `001_initial_schema.py` creates all tables; running twice does not drop data

**Files to Create**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/app/models/truck.py`
- `backend/app/models/driver.py`
- `backend/app/models/load.py`
- `backend/app/models/dwell_event.py`
- `backend/app/models/telemetry_event.py`
- `backend/app/models/alert.py`

**Dependencies**: TASK-002

---

### TASK-004: Pydantic Schemas

**Priority**: P1

**Description**
Create all Pydantic request and response schemas for every domain entity and the dashboard summary. These are used by route handlers for validation and serialization.

**Acceptance Criteria**
- [~] Request schemas (Create/Update) and response schemas defined for: trucks, drivers, loads, dwell_events, telemetry_events, alerts
- [~] `DashboardSummary` response schema includes: `active_trucks`, `avg_dwell_hours`, `total_revenue`, `avg_revenue_per_mile`, `deadhead_percentage`, `open_alerts`, `open_loads`, `fuel_cost_per_mile`
- [~] `LoadProfitability` response schema includes: `load_id`, `revenue`, `miles`, `deadhead_miles`, `revenue_per_mile`, `deadhead_percentage`, `net_profit`
- [~] `FacilityScorecard` response schema includes: `facility_name`, `avg_dwell_hours`, `avg_loading_delay_hours`, `total_detention_pay`, `visit_count`, `facility_score`
- [~] `BrokerScorecard` response schema includes: `broker_name`, `avg_dwell_hours`, `avg_loading_delay_hours`, `total_detention_pay`, `load_count`
- [~] All datetime fields typed as `datetime` with UTC enforcement
- [~] All schemas use Python type hints throughout

**Files to Create**
- `backend/app/schemas/truck.py`
- `backend/app/schemas/driver.py`
- `backend/app/schemas/load.py`
- `backend/app/schemas/dwell_event.py`
- `backend/app/schemas/telemetry_event.py`
- `backend/app/schemas/alert.py`
- `backend/app/schemas/dashboard.py`

**Dependencies**: TASK-003

---

### TASK-005: Repository Layer

**Priority**: P1

**Description**
Implement all repository classes that encapsulate database query logic. Services will call these; no raw SQL outside repositories.

**Acceptance Criteria**
- [~] `TruckRepository`: `get_all()`, `get_by_truck_id()`, `get_active_count()`, `update_position(truck_id, lat, lon, last_seen_at)` — updates `current_lat`, `current_lon`, and `last_seen_at` atomically
- [~] `LoadRepository`: `create()`, `get_all(limit, offset, start_date?, end_date?)`, `get_by_id()`, `get_delivered_totals()` (sum revenue, miles, fuel, deadhead)
- [~] `TelemetryRepository`: `insert()`, `get_by_truck_id(limit, offset)`
- [~] `DwellRepository`: `insert()`, `get_all(limit, offset)`, `get_facility_scorecard(start_date?, end_date?)`, `get_broker_scorecard()`
- [~] `AlertRepository`: `get_all(limit, offset, resolved?)`, `get_by_id()`, `create()`, `resolve()`, `exists_unresolved(truck_id, alert_type)`
- [~] All repositories accept a SQLAlchemy `Session` as a constructor argument
- [~] No business logic in repositories — query logic only

**Files to Create**
- `backend/app/repositories/base.py`
- `backend/app/repositories/truck_repository.py`
- `backend/app/repositories/load_repository.py`
- `backend/app/repositories/telemetry_repository.py`
- `backend/app/repositories/dwell_repository.py`
- `backend/app/repositories/alert_repository.py`

**Dependencies**: TASK-004

---

### TASK-006: Alert Service

**Priority**: P1

**Description**
Implement the `AlertService` with all threshold-based alert generation logic and deduplication. This service is called as a side-effect during telemetry and dwell event ingestion.

**Acceptance Criteria**
- [~] `check_telemetry_alerts(telemetry_event)` triggers:
  - `low_fuel` (medium) if `fuel_level < 15`
  - `engine_overheat` (high) if `engine_temp > 230`
  - `reefer_temp_deviation` (high) if `reefer_temp` outside 34–38°F
- [~] `check_dwell_alert(dwell_event, dwell_hours)` triggers:
  - `high_dwell` (medium) if `dwell_hours > 4`
- [~] Before creating any alert, calls `AlertRepository.exists_unresolved(truck_id, alert_type)` — skips creation if duplicate exists
- [~] All alert messages are human-readable (e.g. "Fuel level at 12% for truck T-001")
- [~] Service methods accept a DB session and call `AlertRepository` only — no direct SQL

**Files to Create**
- `backend/app/services/alert_service.py`

**Dependencies**: TASK-005

---

### TASK-007: Dwell Service and API

**Priority**: P1

**Description**
Implement the dwell service with KPI calculations and the three dwell API endpoints.

**Acceptance Criteria**
- [~] `DwellService.calculate_dwell_hours(arrival, departure)` returns float hours
- [~] `DwellService.calculate_loading_delay(appointment, loading_start)` returns float hours
- [~] `DwellService.calculate_facility_score(avg_dwell_hours)` returns `max(0, 100 - avg_dwell_hours * 10)`
- [~] `POST /api/dwell` — validates `arrival_time < departure_time` (HTTP 422 if not), stores event, triggers alert check, returns HTTP 201
- [~] `GET /api/dwell/events` — returns all events ordered by `arrival_time` desc, supports `limit`/`offset`
- [~] `GET /api/dwell/facility-scorecard` — returns per-facility aggregates, supports `start_date`/`end_date`
- [~] `GET /api/dwell/broker-scorecard` — returns per-broker aggregates

**Files to Create**
- `backend/app/services/dwell_service.py`
- `backend/app/routers/dwell.py`

**Dependencies**: TASK-006

---

### TASK-008: Truck and Telemetry API

**Priority**: P1

**Description**
Implement truck list and telemetry ingestion/query endpoints.

**Acceptance Criteria**
- [~] `GET /api/trucks` — returns all trucks with `truck_id`, `status`, `current_location`, `current_lat`, `current_lon`, `last_seen_at`
- [~] `POST /api/telemetry` — stores telemetry event, triggers alert check via `AlertService`, calls `TruckRepository.update_position(truck_id, gps_lat, gps_lon, timestamp)` to keep truck position current, returns HTTP 201; HTTP 422 on missing required fields
- [~] `GET /api/telemetry/{truck_id}` — returns telemetry ordered by `timestamp` desc, supports `limit`/`offset`; HTTP 404 if truck not found

**Files to Create**
- `backend/app/services/truck_service.py`
- `backend/app/services/telemetry_service.py`
- `backend/app/routers/trucks.py`
- `backend/app/routers/telemetry.py`

**Dependencies**: TASK-006

---

### TASK-009: Alert API

**Priority**: P1

**Description**
Implement the alerts list and resolve endpoints.

**Acceptance Criteria**
- [~] `GET /api/alerts` — returns alerts ordered by `created_at` desc, supports `limit`/`offset`, supports `?resolved=false` filter
- [~] `PATCH /api/alerts/{alert_id}/resolve` — sets `resolved = true`, returns HTTP 200; HTTP 404 if not found

**Files to Create**
- `backend/app/routers/alerts.py`

**Dependencies**: TASK-005

---

### TASK-010: Dashboard Summary API

**Priority**: P1

**Description**
Implement the `DashboardService` and the `/api/dashboard/summary` endpoint that returns all top-level KPIs in a single request.

**Acceptance Criteria**
- [~] `GET /api/dashboard/summary` returns all 8 KPIs: `active_trucks`, `avg_dwell_hours`, `total_revenue`, `avg_revenue_per_mile`, `deadhead_percentage`, `open_alerts`, `open_loads`, `fuel_cost_per_mile`
- [~] Supports optional `start_date` and `end_date` query parameters; all KPIs computed within that window when provided
- [~] All KPI calculations are in `DashboardService` — no logic in the route handler
- [~] Response time under 500ms on standard seed dataset

**Files to Create**
- `backend/app/services/dashboard_service.py`
- `backend/app/routers/dashboard.py`

**Dependencies**: TASK-007, TASK-008, TASK-009

---

### TASK-011: Synthetic Data Simulator

**Priority**: P1

**Description**
Build the CLI seed script that generates realistic synthetic data for all entities and inserts it into the database.

**Acceptance Criteria**
- [~] CLI accepts flags: `--trucks`, `--drivers`, `--loads`, `--dwell-events`, `--telemetry-events`, `--alerts`, `--start-date`, `--end-date`, `--alert-frequency`, `--seed`
- [~] Generates at minimum: 10 trucks, 10 drivers, 100 loads, 200 dwell events, 5000 telemetry events, 50 alerts
- [~] Dwell events satisfy: `arrival < loading_start < loading_end < departure`
- [~] Telemetry values within bounds: speed 0–80, fuel 0–100%, engine_temp 150–250°F
- [~] Load revenue $500–$5000, miles 50–2000, deadhead 0–500
- [~] Alert types: `high_dwell`, `low_fuel`, `reefer_temp_deviation`, `engine_overheat`; severity levels: low / medium / high
- [~] When run a second time, clears all existing data before re-inserting (no duplicates)
- [~] `--seed` flag makes output fully deterministic (same seed → same data)
- [~] Inserts cover a 30-day historical window by default

**Files to Create**
- `simulator/seed.py`
- `simulator/config.py`
- `simulator/generators/trucks.py`
- `simulator/generators/drivers.py`
- `simulator/generators/loads.py`
- `simulator/generators/dwell_events.py`
- `simulator/generators/telemetry_events.py`
- `simulator/generators/alerts.py`

**Dependencies**: TASK-003

---

### TASK-012: Frontend Project Setup

**Priority**: P1

**Description**
Initialize the Next.js frontend with TypeScript, Tailwind CSS, shared layout, navigation, and typed API client.

**Acceptance Criteria**
- [~] Next.js 14+ project with App Router, TypeScript strict mode enabled
- [~] Tailwind CSS configured
- [~] Recharts installed for charting
- [~] `lib/api.ts` contains typed async fetch wrappers for every API endpoint; base URL from `NEXT_PUBLIC_API_URL`
- [~] `types/index.ts` defines TypeScript interfaces for all API response shapes
- [~] `Sidebar` component renders navigation links to: Dashboard, Dwell, Trucks, Loads, Alerts
- [~] `ErrorMessage` component renders user-visible API error
- [~] `LoadingSpinner` component renders loading state
- [~] Root layout wraps all pages with Sidebar + Topbar

**Files to Create**
- `frontend/Dockerfile`
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/next.config.js`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/utils.ts`
- `frontend/src/types/index.ts`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Topbar.tsx`
- `frontend/src/components/ui/ErrorMessage.tsx`
- `frontend/src/components/ui/LoadingSpinner.tsx`

**Dependencies**: TASK-001

---

### TASK-013: Dashboard Landing Page (`/dashboard`)

**Priority**: P1

**Description**
Build the dashboard landing page with seven KPI summary cards.

**Acceptance Criteria**
- [~] Page at `/dashboard` route fetches `GET /api/dashboard/summary` on mount
- [~] Displays seven `KpiCard` components: Active Trucks, Open Loads, Avg Dwell Time, Revenue per Mile, Deadhead %, Fuel Cost per Mile, Open Alerts
- [~] Shows `LoadingSpinner` while fetching
- [~] Shows `ErrorMessage` if API call fails — no blank cards
- [~] Cards are responsive (grid layout, wraps on smaller screens)

**Files to Create**
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/components/cards/KpiCard.tsx`

**Dependencies**: TASK-010, TASK-012

---

### TASK-014: Dwell Analytics Page (`/dwell`)

**Priority**: P1

**Description**
Build the dwell analytics page with facility scorecard table and three charts.

**Acceptance Criteria**
- [~] Page at `/dwell` route
- [~] Fetches `GET /api/dwell/facility-scorecard` and `GET /api/dwell/broker-scorecard` on mount
- [~] **Facility Scorecard Table** — columns: Facility, Broker, Avg Wait Time, Detention Pay, Visits, Score; sortable by Score
- [~] **Top 10 Worst Facilities Bar Chart** — bars ranked by avg dwell hours descending
- [~] **Avg Dwell by Broker Bar Chart** — one bar per broker
- [~] **Detention Pay Chart** — side-by-side bars: recovered vs lost detention pay per facility
- [~] Loading and error states handled

**Files to Create**
- `frontend/src/app/dwell/page.tsx`
- `frontend/src/components/tables/FacilityScorecard.tsx`
- `frontend/src/components/charts/DwellBarChart.tsx`
- `frontend/src/components/charts/BrokerBarChart.tsx`
- `frontend/src/components/charts/DetentionChart.tsx`

**Dependencies**: TASK-007, TASK-012

---

### TASK-015: Alerts Page (`/alerts`)

**Priority**: P1

**Description**
Build the alerts page with severity color-coding, status filter, and inline resolve action.

**Acceptance Criteria**
- [~] Page at `/alerts` route fetches `GET /api/alerts` on mount
- [~] Table columns: Truck ID, Severity, Type, Message, Created At, Status
- [~] `SeverityBadge` component: red for high, orange for medium, yellow for low
- [~] Filter control (toggle/dropdown): All / Open / Resolved — passes `?resolved=false` to API when filtered
- [~] "Resolve" button visible on unresolved rows; fires `PATCH /api/alerts/{id}/resolve`; updates row in-place without full page reload
- [ ] Loading and error states handled

**Files to Create**
- `frontend/src/app/alerts/page.tsx`
- `frontend/src/components/tables/AlertsTable.tsx`
- `frontend/src/components/ui/SeverityBadge.tsx`

**Dependencies**: TASK-009, TASK-012

---

## Phase 2 Tasks

---

### TASK-016: Load Service and API

**Priority**: P2

**Description**
Implement the load service with profitability calculations and all load API endpoints.

**Acceptance Criteria**
- [~] `POST /api/loads` — stores load, returns HTTP 201; HTTP 422 on validation failure
- [~] `GET /api/loads` — returns loads ordered by `pickup_time` desc, supports `limit`/`offset`, supports `start_date`/`end_date` filter
- [~] `GET /api/loads/{load_id}/profitability` — returns profitability report; HTTP 404 if not found
- [~] `LoadService.calculate_revenue_per_mile(revenue, miles)` → `revenue / miles`
- [~] `LoadService.calculate_deadhead_percentage(deadhead_miles, miles)` → `(deadhead_miles / miles) * 100`
- [~] `LoadService.calculate_net_profit(load)` → `revenue - (fuel_cost + maintenance_reserve + driver_cost + tolls)`
- [~] All calculation logic in `LoadService` — no logic in route handler

**Files to Create**
- `backend/app/services/load_service.py`
- `backend/app/routers/loads.py`

**Dependencies**: TASK-005

---

### TASK-017: Load Profitability Page (`/loads`)

**Priority**: P2

**Description**
Build the load profitability page with a full load table and per-load detail view.

**Acceptance Criteria**
- [~] Page at `/loads` route fetches `GET /api/loads` on mount
- [~] Table columns: Load ID, Broker, Origin, Destination, Revenue, Miles, RPM, Deadhead %, Status
- [~] Clicking a row fetches `GET /api/loads/{load_id}/profitability` and displays the full report in a slide-over panel or modal
- [~] Profitability detail shows: Revenue, Miles, Deadhead Miles, Revenue per Mile, Deadhead %, Net Profit
- [~] Loading and error states handled for both table and detail panel

**Files to Create**
- `frontend/src/app/loads/page.tsx`
- `frontend/src/components/tables/LoadsTable.tsx`

**Dependencies**: TASK-016, TASK-012

---

### TASK-018: Truck Status Page (`/trucks`)

**Priority**: P2

**Description**
Build the truck status page with color-coded status indicators.

**Acceptance Criteria**
- [~] Page at `/trucks` route fetches `GET /api/trucks` on mount
- [~] Table columns: Truck ID, Status, Current Location, Last Seen At
- [~] `current_lat` and `current_lon` are stored in the API response and available for future map integration but not rendered in the MVP table view
- [~] `StatusBadge` component: green for active, yellow for idle, red for maintenance
- [ ] Loading and error states handled

**Files to Create**
- `frontend/src/app/trucks/page.tsx`
- `frontend/src/components/tables/TrucksTable.tsx`
- `frontend/src/components/ui/StatusBadge.tsx`

**Dependencies**: TASK-008, TASK-012

---

## Task Summary

| Task | Title | Phase | Priority | Depends On |
|---|---|---|---|---|
| TASK-001 | Project Scaffolding + Docker Compose | 1 | P0 | — |
| TASK-002 | FastAPI App Init + Middleware | 1 | P0 | 001 |
| TASK-003 | Database Schema + Alembic Migration | 1 | P0 | 002 |
| TASK-004 | Pydantic Schemas | 1 | P1 | 003 |
| TASK-005 | Repository Layer | 1 | P1 | 004 |
| TASK-006 | Alert Service | 1 | P1 | 005 |
| TASK-007 | Dwell Service + API | 1 | P1 | 006 |
| TASK-008 | Truck + Telemetry API | 1 | P1 | 006 |
| TASK-009 | Alert API | 1 | P1 | 005 |
| TASK-010 | Dashboard Summary API | 1 | P1 | 007, 008, 009 |
| TASK-011 | Synthetic Data Simulator | 1 | P1 | 003 |
| TASK-012 | Frontend Setup + API Client | 1 | P1 | 001 |
| TASK-013 | Dashboard Landing Page | 1 | P1 | 010, 012 |
| TASK-014 | Dwell Analytics Page | 1 | P1 | 007, 012 |
| TASK-015 | Alerts Page | 1 | P1 | 009, 012 |
| TASK-016 | Load Service + API | 2 | P2 | 005 |
| TASK-017 | Load Profitability Page | 2 | P2 | 016, 012 |
| TASK-018 | Truck Status Page | 2 | P2 | 008, 012 |

## Recommended Execution Order

```
TASK-001
  └── TASK-002
        └── TASK-003
              ├── TASK-004
              │     └── TASK-005
              │           ├── TASK-006
              │           │     ├── TASK-007 ──┐
              │           │     └── TASK-008   ├── TASK-010
              │           └── TASK-009 ─────────┘
              │                                      └── TASK-013
              └── TASK-011             TASK-014 ──────────────┘
                                       TASK-015

TASK-001
  └── TASK-012
        ├── TASK-013 (waits for TASK-010)
        ├── TASK-014 (waits for TASK-007)
        └── TASK-015 (waits for TASK-009)
```

Backend (TASK-001 through TASK-011) and Frontend setup (TASK-012) can be worked in parallel once TASK-001 is done.