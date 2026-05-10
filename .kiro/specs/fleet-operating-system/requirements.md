# Requirements Document

## Introduction

The Fleet Operating System (Fleet OS) is an internal trucking operations intelligence dashboard that ingests simulated trucking events, stores them in a PostgreSQL database via a FastAPI backend, calculates key performance indicators (KPIs), and presents them through a React/Next.js dashboard. The MVP focuses on the Dwell-Time Analytics module using synthetic/mock data only — no real truck integrations. The system enables dispatchers and operations managers to monitor truck status, analyze facility and broker performance, track load profitability, and respond to operational alerts from a single interface.

## Glossary

- **Fleet_OS**: The Fleet Operating System — the full application described in this document.
- **Dashboard**: The React/Next.js frontend application that displays KPIs and operational data.
- **API**: The FastAPI backend application that exposes REST endpoints.
- **Simulator**: The Python module that generates synthetic trucking events and seeds the database.
- **Truck**: A simulated commercial vehicle identified by a unique `truck_id`.
- **Driver**: A simulated driver identified by a unique `driver_id`.
- **Load**: A freight assignment from an origin to a destination with associated revenue and mileage data.
- **Dwell_Event**: A record capturing a truck's time at a facility, including arrival, loading start/end, and departure timestamps.
- **Telemetry_Event**: A time-series record of a truck's sensor readings (speed, RPM, fuel level, GPS, etc.).
- **Alert**: A system-generated notification triggered when a KPI or sensor reading crosses a defined threshold.
- **Facility**: A physical location (shipper or receiver) where loading or unloading occurs.
- **Broker**: A freight broker who tenders loads to the carrier.
- **Dwell_Time**: The total elapsed time between a truck's arrival at a facility and its departure.
- **Loading_Delay**: The elapsed time between the scheduled appointment and the actual loading start.
- **Detention_Pay**: Compensation owed to the carrier when a truck is held at a facility beyond the free-time window.
- **Deadhead_Miles**: Miles driven without a loaded trailer.
- **Deadhead_Percentage**: The ratio of deadhead miles to total miles, expressed as a percentage.
- **Revenue_Per_Mile**: Load revenue divided by total miles driven on that load.
- **Net_Profit**: Revenue minus fuel cost, maintenance reserve, driver cost, and tolls for a given load.
- **Facility_Score**: A numeric score from 0–100 representing facility performance, penalized by average dwell hours.
- **KPI**: Key Performance Indicator — a measurable value used to evaluate operational performance.
- **Fuel_Cost**: The total fuel expense for a given load, stored in the `loads` table.
- **Maintenance_Reserve**: A per-load cost allocation for vehicle maintenance, stored in the `loads` table.
- **Driver_Cost**: The driver pay allocated to a given load, stored in the `loads` table.
- **Tolls**: Road toll charges incurred on a given load, stored in the `loads` table.
- **Current_Lat**: The most recently recorded GPS latitude of a truck, stored in the `trucks` table.
- **Current_Lon**: The most recently recorded GPS longitude of a truck, stored in the `trucks` table.
- **Last_Seen_At**: The UTC timestamp of the most recent telemetry event received for a truck, stored in the `trucks` table.

---

## Requirements

### Requirement 1: Project Infrastructure and Local Development Environment

**User Story:** As a developer, I want a Docker Compose environment that starts all services together, so that I can run the full stack locally with a single command.

#### Acceptance Criteria

1. THE Fleet_OS SHALL include a `docker-compose.yml` file that defines services for the API, PostgreSQL database, and Dashboard.
2. WHEN `docker-compose up` is executed, THE Fleet_OS SHALL start all three services and make the API reachable on port 8000 and the Dashboard reachable on port 3000.
3. THE Fleet_OS SHALL include a `README.md` with step-by-step instructions for starting the local environment.
4. IF the PostgreSQL service is not yet ready when the API starts, THEN THE API SHALL retry the database connection until it succeeds or a 30-second timeout is reached.
5. Authentication and authorization are out of scope for MVP Phase 1; however, THE Fleet_OS SHALL design all API routes to support JWT-based authentication in future phases without requiring structural changes to the route definitions.
6. THE API SHALL expose a `GET /health` endpoint that returns HTTP 200 with a JSON body indicating database connectivity status and service uptime, suitable for use by Docker health checks and monitoring systems.
7. THE API SHALL expose auto-generated Swagger/OpenAPI documentation at `/docs`, provided by FastAPI's built-in OpenAPI integration, accessible when the API service is running.
8. THE API SHALL enable configurable CORS (Cross-Origin Resource Sharing) support so that the frontend application running on a different port during local development can make requests to the API without browser CORS errors. The allowed origins SHALL be configurable via environment variable.
9. THE Fleet_OS SHALL load all runtime configuration from environment variables, including at minimum: `DATABASE_URL` (PostgreSQL connection string), `API_PORT` (default 8000), `FRONTEND_URL` (used for CORS allowed origins), and `LOG_LEVEL` (default `info`). A `.env.example` file SHALL document all required and optional environment variables.
10. THE `docker-compose.yml` SHALL define a named Docker volume for the PostgreSQL service so that database data persists across container restarts and `docker-compose down` operations without data loss.

---

### Requirement 2: Database Schema

**User Story:** As a developer, I want a well-defined PostgreSQL schema with all required tables, so that all trucking data can be stored and queried reliably.

#### Acceptance Criteria

1. THE Fleet_OS SHALL create a `trucks` table with columns: `id`, `truck_id`, `status`, `current_location`, `current_lat`, `current_lon`, `last_seen_at`, `created_at`.
2. THE Fleet_OS SHALL create a `drivers` table with columns: `id`, `driver_id`, `name`, `status`.
3. THE Fleet_OS SHALL create a `loads` table with columns: `id`, `load_id`, `truck_id`, `driver_id`, `broker_name`, `origin`, `destination`, `revenue`, `miles`, `deadhead_miles`, `fuel_cost`, `maintenance_reserve`, `driver_cost`, `tolls`, `pickup_time`, `delivery_time`, `status`.
4. THE Fleet_OS SHALL create a `dwell_events` table with columns: `id`, `load_id`, `facility_name`, `broker_name`, `appointment_time`, `arrival_time`, `loading_start`, `loading_end`, `departure_time`, `detention_pay`, `driver_notes`.
5. THE Fleet_OS SHALL create a `telemetry_events` table with columns: `id`, `truck_id`, `timestamp`, `speed`, `rpm`, `engine_temp`, `fuel_level`, `gps_lat`, `gps_lon`, `idle_minutes`, `reefer_temp`, `load_weight`.
6. THE Fleet_OS SHALL create an `alerts` table with columns: `id`, `truck_id`, `severity`, `alert_type`, `message`, `created_at`, `resolved`.
7. THE Fleet_OS SHALL include a migration script that creates all tables in an empty PostgreSQL database.
8. WHEN the migration script is run against an already-initialized database, THE Fleet_OS SHALL apply only the missing schema changes without dropping existing data.
9. THE Fleet_OS SHALL define a foreign key constraint on `loads.truck_id` referencing `trucks.truck_id`.
10. THE Fleet_OS SHALL define a foreign key constraint on `loads.driver_id` referencing `drivers.driver_id`.
11. THE Fleet_OS SHALL define a foreign key constraint on `dwell_events.load_id` referencing `loads.load_id`.
12. THE Fleet_OS SHALL define a foreign key constraint on `telemetry_events.truck_id` referencing `trucks.truck_id`.
13. THE Fleet_OS SHALL define a foreign key constraint on `alerts.truck_id` referencing `trucks.truck_id`.
14. THE Fleet_OS SHALL create a composite index on `telemetry_events(truck_id, timestamp)` to support efficient per-truck time-series queries.
15. THE Fleet_OS SHALL create an index on `dwell_events(arrival_time)` to support date-range filtering.
16. THE Fleet_OS SHALL create an index on `loads(pickup_time)` to support date-range filtering.
17. THE Fleet_OS SHALL create a composite index on `alerts(created_at, resolved)` to support filtered alert queries.
18. ALL timestamps stored in the database SHALL be in UTC. THE API SHALL accept and return all timestamps in UTC ISO 8601 format.
19. WHEN a telemetry event is ingested for a truck, THE API SHALL update that truck's `current_lat`, `current_lon`, and `last_seen_at` fields in the `trucks` table with the values from the telemetry event.

---

### Requirement 3: Synthetic Data Simulation

**User Story:** As a developer, I want a simulator that generates realistic synthetic trucking data, so that the dashboard can be demonstrated and tested without connecting to real trucks.

#### Acceptance Criteria

1. THE Simulator SHALL generate synthetic records for trucks, drivers, loads, dwell events, telemetry events, and alerts covering a 30-day historical window.
2. WHEN the seed script is executed, THE Simulator SHALL insert at least 10 trucks, 10 drivers, 100 loads, 200 dwell events, 5000 telemetry events, and 50 alerts into the database.
3. THE Simulator SHALL generate `dwell_events` where `arrival_time` is before `loading_start`, `loading_start` is before `loading_end`, and `loading_end` is before `departure_time`.
4. THE Simulator SHALL generate `telemetry_events` with `speed` values between 0 and 80 mph, `fuel_level` values between 0 and 100 percent, and `engine_temp` values between 150 and 250 degrees Fahrenheit.
5. THE Simulator SHALL generate `loads` where `revenue` is between $500 and $5000, `miles` is between 50 and 2000, and `deadhead_miles` is between 0 and 500.
6. THE Simulator SHALL generate alerts of severity levels `low`, `medium`, and `high` with alert types including `high_dwell`, `low_fuel`, `reefer_temp_deviation`, and `engine_overheat`.
7. WHEN the seed script is run a second time, THE Simulator SHALL clear existing synthetic data before re-inserting to prevent duplicate records.
8. THE Simulator SHALL accept configuration parameters for: truck count, driver count, load count, dwell event count, telemetry event count, alert count, date range start, date range end, and alert frequency — so that the seed dataset can be adjusted without modifying source code.
9. THE Simulator SHALL support an optional `--seed` parameter that sets the random number generator seed, enabling deterministic dataset generation so that the same seed value always produces identical synthetic records for reproducible testing and debugging.

---

### Requirement 4: Telemetry Ingestion API

**User Story:** As a dispatcher, I want the system to ingest truck telemetry events, so that real-time sensor data can be stored and monitored.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/api/telemetry` with a valid telemetry payload, THE API SHALL store the telemetry event in the `telemetry_events` table and return HTTP 201.
2. IF a POST request to `/api/telemetry` contains a missing required field, THEN THE API SHALL return HTTP 422 with a descriptive validation error message.
3. WHEN a GET request is sent to `/api/telemetry/{truck_id}`, THE API SHALL return all telemetry events for that truck ordered by `timestamp` descending.
4. IF a GET request is sent to `/api/telemetry/{truck_id}` for a `truck_id` that does not exist, THEN THE API SHALL return HTTP 404.
5. WHEN a GET request is sent to `/api/trucks`, THE API SHALL return a list of all trucks with their current `status` and `current_location`.
6. WHEN a GET request is sent to `/api/telemetry/{truck_id}`, THE API SHALL support optional `limit` and `offset` query parameters for pagination, defaulting to a maximum of 100 records per request.

---

### Requirement 5: Dwell Event API

**User Story:** As a dispatcher, I want to record and query dwell events at facilities, so that I can identify which facilities and brokers cause the most delays.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/api/dwell` with a valid dwell event payload, THE API SHALL store the dwell event in the `dwell_events` table and return HTTP 201.
2. IF a POST request to `/api/dwell` contains an `arrival_time` that is after `departure_time`, THEN THE API SHALL return HTTP 422 with a descriptive error message.
3. WHEN a GET request is sent to `/api/dwell/events`, THE API SHALL return all dwell events ordered by `arrival_time` descending.
4. WHEN a GET request is sent to `/api/dwell/facility-scorecard`, THE API SHALL return one record per facility containing: `facility_name`, `avg_dwell_hours`, `avg_loading_delay_hours`, `total_detention_pay`, `visit_count`, and `facility_score`.
5. WHEN a GET request is sent to `/api/dwell/broker-scorecard`, THE API SHALL return one record per broker containing: `broker_name`, `avg_dwell_hours`, `avg_loading_delay_hours`, `total_detention_pay`, and `load_count`.
6. THE Dwell_Service SHALL calculate `dwell_time` as `departure_time` minus `arrival_time` expressed in hours.
7. THE Dwell_Service SHALL calculate `loading_delay` as `loading_start` minus `appointment_time` expressed in hours.
8. THE Dwell_Service SHALL calculate `facility_score` as `max(0, 100 - avg_dwell_hours * 10)`, so that a 2-hour average dwell scores 80, a 5-hour average dwell scores 50, and a 10-hour average dwell scores 0.
9. WHEN a GET request is sent to `/api/dwell/facility-scorecard` with optional `start_date` and `end_date` query parameters, THE API SHALL filter dwell events to only those with `arrival_time` within the specified date range before computing scorecard metrics.
10. WHEN a GET request is sent to `/api/dwell/events`, THE API SHALL support optional `limit` and `offset` query parameters for pagination, defaulting to a maximum of 100 records per request.

---

### Requirement 6: Load API

**User Story:** As an operations manager, I want to create and query loads with profitability data, so that I can evaluate the financial performance of each freight assignment.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/api/loads` with a valid load payload, THE API SHALL store the load in the `loads` table and return HTTP 201.
2. WHEN a GET request is sent to `/api/loads`, THE API SHALL return all loads ordered by `pickup_time` descending.
3. WHEN a GET request is sent to `/api/loads` with optional `start_date` and `end_date` query parameters, THE API SHALL return only loads with `pickup_time` within the specified date range.
4. WHEN a GET request is sent to `/api/loads/{load_id}/profitability`, THE API SHALL return a profitability report for that load containing: `load_id`, `revenue`, `miles`, `deadhead_miles`, `revenue_per_mile`, `deadhead_percentage`, and `net_profit`.
5. IF a GET request is sent to `/api/loads/{load_id}/profitability` for a `load_id` that does not exist, THEN THE API SHALL return HTTP 404.
6. THE Analytics_Service SHALL calculate `revenue_per_mile` as `revenue` divided by `miles`.
7. THE Analytics_Service SHALL calculate `deadhead_percentage` as `deadhead_miles` divided by `miles` multiplied by 100.
8. THE Analytics_Service SHALL calculate `net_profit` as `revenue` minus the sum of fuel cost, maintenance reserve, driver cost, and tolls for that load.
9. WHEN a GET request is sent to `/api/loads`, THE API SHALL support optional `limit` and `offset` query parameters for pagination, defaulting to a maximum of 100 records per request.

---

### Requirement 7: Dashboard Summary API

**User Story:** As a dispatcher, I want a single API endpoint that returns all top-level KPIs, so that the dashboard landing page can load its summary cards in one request.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/dashboard/summary` with optional `start_date` and `end_date` query parameters, THE API SHALL return a JSON object containing: `active_trucks`, `avg_dwell_hours`, `total_revenue`, `avg_revenue_per_mile`, `deadhead_percentage`, `open_alerts`, `open_loads`, and `fuel_cost_per_mile`.
2. THE API SHALL calculate `active_trucks` as the count of trucks with `status` equal to `active`.
3. THE API SHALL calculate `avg_dwell_hours` as the mean dwell time across all dwell events in the database.
4. THE API SHALL calculate `total_revenue` as the sum of `revenue` across all loads with `status` equal to `delivered`.
5. THE API SHALL calculate `avg_revenue_per_mile` as the mean of `revenue_per_mile` across all delivered loads.
6. THE API SHALL calculate `deadhead_percentage` as the total `deadhead_miles` divided by total `miles` across all delivered loads, multiplied by 100.
7. THE API SHALL calculate `open_alerts` as the count of alerts where `resolved` is false.
8. THE API SHALL calculate `open_loads` as the count of loads with `status` not equal to `delivered` or `cancelled`.
9. THE API SHALL calculate `fuel_cost_per_mile` as the total `fuel_cost` divided by total `miles` across all delivered loads.
10. WHEN `start_date` and `end_date` query parameters are provided to `/api/dashboard/summary`, THE API SHALL compute all KPIs using only data within the specified date range.

---

### Requirement 8: Alert API and Alert Generation

**User Story:** As a dispatcher, I want the system to automatically generate alerts when KPIs or sensor readings cross defined thresholds, so that I can respond to operational issues before they escalate.

#### Acceptance Criteria

1. WHEN a GET request is sent to `/api/alerts`, THE API SHALL return all alerts ordered by `created_at` descending.
2. WHEN a GET request is sent to `/api/alerts?resolved=false`, THE API SHALL return only unresolved alerts.
3. WHEN a PATCH request is sent to `/api/alerts/{alert_id}/resolve`, THE API SHALL set `resolved` to true for that alert and return HTTP 200.
4. IF a PATCH request is sent to `/api/alerts/{alert_id}/resolve` for an `alert_id` that does not exist, THEN THE API SHALL return HTTP 404.
5. WHEN a telemetry event is ingested with `fuel_level` below 15 percent, THE Alert_Service SHALL create a `low_fuel` alert of severity `medium` for that truck.
6. WHEN a telemetry event is ingested with `engine_temp` above 230 degrees Fahrenheit, THE Alert_Service SHALL create an `engine_overheat` alert of severity `high` for that truck.
7. WHEN a telemetry event is ingested with `reefer_temp` outside the range of 34 to 38 degrees Fahrenheit, THE Alert_Service SHALL create a `reefer_temp_deviation` alert of severity `high` for that truck.
8. WHEN a dwell event is saved with a dwell time exceeding 4 hours, THE Alert_Service SHALL create a `high_dwell` alert of severity `medium` for the associated load.
9. IF an unresolved alert of the same `alert_type` already exists for the same `truck_id`, THEN THE Alert_Service SHALL NOT create a duplicate alert.
10. WHEN a GET request is sent to `/api/alerts`, THE API SHALL support optional `limit` and `offset` query parameters for pagination, defaulting to a maximum of 100 records per request.

---

### Requirement 9: Dashboard Landing Page

**User Story:** As a dispatcher, I want a dashboard landing page that shows all top-level KPIs at a glance, so that I can quickly assess the current state of fleet operations.

#### Acceptance Criteria

1. THE Dashboard SHALL display a landing page at the `/dashboard` route containing summary cards for: Active Trucks, Open Loads, Average Dwell Time, Revenue per Mile, Deadhead %, Fuel Cost per Mile, and Open Alerts.
2. WHEN the landing page loads, THE Dashboard SHALL fetch data from `GET /api/dashboard/summary` and populate the summary cards.
3. WHEN the API returns an error, THE Dashboard SHALL display a user-visible error message instead of blank cards.
4. THE Dashboard SHALL include a navigation menu linking to the Dashboard, Dwell, Loads, Trucks, and Alerts pages.

---

### Requirement 10: Dwell Analytics Page

**User Story:** As an operations manager, I want a dedicated dwell analytics page with charts and scorecards, so that I can identify the worst-performing facilities and brokers.

#### Acceptance Criteria

1. THE Dashboard SHALL display a dwell analytics page at the `/dwell` route.
2. THE Dashboard SHALL display a facility scorecard table with columns: Facility, Broker, Avg Wait Time, Detention Pay, Number of Visits, and Score.
3. THE Dashboard SHALL display a bar chart showing the top 10 worst facilities ranked by average dwell time.
4. THE Dashboard SHALL display a bar chart showing average dwell time grouped by broker.
5. THE Dashboard SHALL display a chart comparing detention pay recovered versus detention pay lost.
6. WHEN the dwell page loads, THE Dashboard SHALL fetch data from `GET /api/dwell/facility-scorecard` and `GET /api/dwell/broker-scorecard` to populate the table and charts.

---

### Requirement 11: Truck Status Page

**User Story:** As a dispatcher, I want a truck status page that shows the current state of every truck in the fleet, so that I can monitor availability and location at a glance.

#### Acceptance Criteria

1. THE Dashboard SHALL display a truck status page at the `/trucks` route.
2. WHEN the trucks page loads, THE Dashboard SHALL fetch data from `GET /api/trucks` and display each truck's `truck_id`, `status`, and `current_location`.
3. THE Dashboard SHALL visually distinguish trucks by status using color-coded indicators (e.g., green for active, yellow for idle, red for maintenance).

---

### Requirement 12: Load Profitability Page

**User Story:** As an operations manager, I want a load profitability page that lists all loads with their financial metrics, so that I can identify which loads are most and least profitable.

#### Acceptance Criteria

1. THE Dashboard SHALL display a load profitability page at the `/loads` route.
2. WHEN the loads page loads, THE Dashboard SHALL fetch data from `GET /api/loads` and display each load's `load_id`, `broker_name`, `origin`, `destination`, `revenue`, `miles`, `revenue_per_mile`, `deadhead_percentage`, and `status`.
3. THE Dashboard SHALL allow the user to click on a load row to view the full profitability report fetched from `GET /api/loads/{load_id}/profitability`.

---

### Requirement 13: Alerts Page

**User Story:** As a dispatcher, I want an alerts page that lists all open and resolved alerts, so that I can track and resolve operational issues.

#### Acceptance Criteria

1. THE Dashboard SHALL display an alerts page at the `/alerts` route.
2. WHEN the alerts page loads, THE Dashboard SHALL fetch data from `GET /api/alerts` and display each alert's `truck_id`, `severity`, `alert_type`, `message`, `created_at`, and `resolved` status.
3. THE Dashboard SHALL visually distinguish alert severity using color-coded indicators (e.g., red for high, orange for medium, yellow for low).
4. WHEN a user clicks a "Resolve" button on an unresolved alert, THE Dashboard SHALL send a PATCH request to `/api/alerts/{alert_id}/resolve` and update the alert's display to show it as resolved without requiring a full page reload.
5. THE Dashboard SHALL allow the user to filter alerts by `resolved` status using a toggle or dropdown control.

---

### Requirement 14: MVP Phase Prioritization

**User Story:** As a developer, I want the MVP to be delivered in two phases so that the most critical operational views are available first.

#### Acceptance Criteria

1. THE Fleet_OS Phase 1 SHALL implement: database schema, simulator/seed script, dashboard summary API, dwell analytics page, and alerts page.
2. THE Fleet_OS Phase 2 SHALL implement: load profitability page, truck status page, and telemetry detail views.
3. WHEN Phase 1 is complete, THE Dashboard SHALL be fully functional for the dwell analytics and alerts use cases even if Phase 2 features are not yet built.

---

### Requirement 15: Architecture Constraints

**User Story:** As a developer, I want the system to follow clear architectural boundaries, so that business logic, data access, and presentation concerns remain separated and maintainable.

#### Acceptance Criteria

1. THE backend SHALL remain stateless — no session state shall be stored in the API process between requests.
2. ALL KPI calculation and business logic SHALL reside in the services layer (`services/`); API route handlers SHALL NOT contain KPI logic.
3. ALL database access SHALL be performed through the service or repository layer; API route handlers SHALL NOT execute raw SQL queries directly.
4. THE frontend SHALL consume data exclusively through the REST API; the frontend SHALL NOT access the database directly.
5. THE backend SHALL use Python type hints throughout and validate all request/response payloads using Pydantic models.
6. THE frontend SHALL be written in TypeScript with strict type checking enabled.
7. THE backend SHALL include a `repositories/` directory under `backend/app/` containing repository classes for each domain entity, including at minimum: `TruckRepository`, `LoadRepository`, `TelemetryRepository`, `DwellRepository`, and `AlertRepository`.
8. Repository classes SHALL encapsulate all database query logic for their respective domain entity; service classes SHALL call repository methods rather than executing queries directly.

---

### Requirement 16: Non-Functional Requirements

**User Story:** As a developer, I want the system to meet defined performance, reliability, and observability standards, so that it remains usable and maintainable as data volume grows.

#### Acceptance Criteria

1. THE API SHALL return responses for all `/api/dashboard/summary` queries in under 500 milliseconds when using the standard seed dataset.
2. THE system SHALL remain fully functional with at least 100,000 telemetry events stored in the database without degradation in query performance.
3. THE Dashboard pages SHALL load and render within 2 seconds when running locally with Docker Compose.
4. THE API SHALL return structured JSON error responses for all 4xx and 5xx errors, including an `error` field with a human-readable message.
5. ALL API request logs SHALL include a `request_id` and `timestamp` field to support tracing and debugging.
6. THE system SHALL be fully runnable locally using `docker-compose up` with no additional manual setup steps beyond those documented in `README.md`.

---

### Requirement 17: Out of Scope for MVP

**User Story:** As a developer, I want a clear list of excluded features, so that the MVP implementation stays focused and does not expand beyond its defined boundaries.

#### Acceptance Criteria

1. THE Fleet_OS MVP SHALL NOT implement real ELD (Electronic Logging Device) integration.
2. THE Fleet_OS MVP SHALL NOT integrate with real GPS data providers.
3. THE Fleet_OS MVP SHALL NOT connect to real freight broker APIs.
4. THE Fleet_OS MVP SHALL NOT implement payment or invoicing systems.
5. THE Fleet_OS MVP SHALL NOT implement user authentication or authorization in Phase 1.
6. THE Fleet_OS MVP SHALL NOT include mobile applications.
7. THE Fleet_OS MVP SHALL NOT include machine learning prediction models or route optimization engines.
8. THE Fleet_OS MVP SHALL NOT support multi-tenant or SaaS deployment configurations.
