# Static Dashboard UI — HTML/CSS Prototype

## Overview

A single-file static dashboard (`frontend/dashboard.html`) that visualizes all key fleet-os data domains in one organized view. Uses only vanilla HTML and CSS — no JavaScript, no dependencies, no build step.

## Purpose

Provides a quick, shareable visual reference for the dashboard layout and data hierarchy without requiring the Next.js app or backend to be running. Useful for design reviews, stakeholder demos, and layout iteration.

## File

```
frontend/dashboard.html
```

Open directly in any browser (`open frontend/dashboard.html`).

## Layout

```
┌──────────┬────────────────────────────────────────┐
│ Sidebar  │ Topbar (title + live badge + date)     │
│          ├────────────────────────────────────────┤
│ - Dash   │ KPI Grid (8 cards, 4-col)              │
│ - Dwell  ├───────────────┬────────────────────────┤
│ - Trucks │ Revenue Chart │ Dwell by Facility Chart │
│ - Alerts ├───────────────┼────────────────────────┤
│ - Loads  │ Truck Table   │ Alert List              │
│ - Drivers├───────────────┴────────────────────────┤
│ - Settings│ Facility Scorecard (full-width table)  │
│          ├────────────────────────────────────────┤
│          │ Broker Scorecard (full-width table)     │
└──────────┴────────────────────────────────────────┘
```

## Sections

### KPI Grid
Eight metric cards, each with a colored top border:
| Metric | Source field |
|---|---|
| Active Trucks | `DashboardSummary.active_trucks` |
| Total Revenue | `DashboardSummary.total_revenue` |
| Open Loads | `DashboardSummary.open_loads` |
| Open Alerts | `DashboardSummary.open_alerts` |
| Avg Dwell Time | `DashboardSummary.avg_dwell_hours` |
| Fuel Cost / Mile | `DashboardSummary.fuel_cost_per_mile` |
| Revenue / Mile | `DashboardSummary.avg_revenue_per_mile` |
| Deadhead % | `DashboardSummary.deadhead_percentage` |

### Revenue by Week (Bar Chart)
CSS-only bar chart showing 6-week revenue trend. Maps to the `/api/dashboard/summary` data aggregated over time windows.

### Avg Dwell by Facility (Bar Chart)
CSS-only bar chart using color coding: green (< 2.5h), amber (2.5–4h), red (> 4h). Sourced from `FacilityScorecard.avg_dwell_hours`.

### Truck Fleet Status Table
Columns: Truck ID, Status badge, Location, Last Seen. Status badges: Active, En Route, Idle, Offline. Maps to `Truck` schema.

### Open Alerts List
Each alert shows truck ID, message, time, and severity badge (Critical / High / Medium / Low). Maps to `Alert` schema, filtered to `resolved = false`.

### Facility Scorecard Table
Columns: Facility, Visits, Avg Dwell (h), Avg Loading Delay (h), Total Detention Pay, Score (progress bar). Maps to `FacilityScorecard` schema from `/api/dwell/facility-scorecard`.

Score color thresholds:
- ≥ 8.0 → green
- 5.0–7.9 → amber
- < 5.0 → red

### Broker Scorecard Table
Columns: Broker, Load Count, Avg Dwell (h), Avg Loading Delay (h), Total Detention Pay. Maps to `BrokerScorecard` schema from `/api/dwell/broker-scorecard`.

## Design Decisions

- **No JavaScript**: all data is hardcoded sample data; the file is a layout/design artifact, not a live view.
- **CSS custom properties**: theming via `:root` variables makes color updates trivial.
- **Responsive grid**: KPI grid collapses to 2-col on narrow viewports; two-column sections stack to single column below 900px.
- **CSS-only bar charts**: avoids Chart.js or Recharts dependency; bars are `div` elements with percentage heights inside a fixed-height flex container.

## Sample Data Sources

All values are representative samples consistent with the simulator's output ranges (see `backend/simulator/generators/`).

## Next Steps (if wiring to live API)

1. Replace hardcoded values with `fetch` calls to `/api/dashboard/summary`, `/api/trucks`, `/api/alerts`, `/api/dwell/facility-scorecard`, `/api/dwell/broker-scorecard`.
2. Add a polling interval (existing `usePolling` hook can be adapted).
3. Replace CSS bar charts with Recharts components already present in the Next.js app.
