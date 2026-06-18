# Dispatch Scoring Framework Implementation Plan

## Context

The current Dispatcher Command Center already has most of the data needed for a layered scoring model, but the implementation mixes eligibility, economics, risk downgrades, and ranking bonuses in one flow.

Current findings:

- `backend/app/services/dispatcher_command_center_service.py` orchestrates load decisioning, filters maintenance/busy trucks, chooses one best available driver, computes deadhead, pickup feasibility, recommendation downgrades, and truck ranking.
- `backend/app/services/load_evaluation_service.py` calculates gross RPM, deadhead-adjusted RPM, estimated fuel cost, revenue/hour, deadhead penalty, net margin, and the current threshold-based `operational_score`.
- `backend/app/services/deadhead.py` supports only haversine deadhead from truck/load coordinates, with stored `load.deadhead_miles` fallback. There is no truck-routing provider in the codebase today.
- `backend/app/services/facility_service.py` already provides facility `avg_dwell_hours`, `p90_dwell_hours`, `detention_risk_band`, visit count, and confidence.
- `backend/app/services/broker_risk.py` provides low/medium/high broker risk from the stored broker name.
- `backend/app/schemas/live_position.py` exposes truck status, coordinates, active alert count, and highest alert severity.
- Existing load/truck/driver models do **not** include driver home base, requested home-time, asset rebalancing targets, real legal route duration, routed tolls per candidate truck, or broker payment/cancel history beyond the existing broker risk band.

Intended outcome: implement a production-shaped scoring framework using only current backend data and derived values. The public standard should move to `RECOMMENDED` / `REVIEW` / `AVOID`, v1 should stay on the existing haversine/stored-deadhead route fallback, and timestamp-backed pickup infeasibility should be a hard blocker.

## Approach

Recommended v1 scope:

1. Introduce a pure scoring layer that separates:
   - Hard eligibility constraints.
   - Continuous load profitability scoring (`Sprofit`).
   - Risk multipliers for facility and broker risk.
   - Alert penalties and existing strategic location/status bonuses.
2. Keep current backend data sources and avoid adding model fields for data the app does not have. Specifically, do **not** implement driver home-time, home-base matching, asset-rebalancing targets, broker payment/cancel history, dynamic fuel indexing, or routed toll enrichment until the backend has those data sources.
3. Treat external truck routing as a future adapter seam only. For this implementation, continue using `truck_deadhead_miles(...)` and the existing average-speed duration estimate, because no routing provider is currently configured.
4. Change the public recommendation standard to:
   - `>= 80` => `RECOMMENDED` (green)
   - `50-79` => `REVIEW` (yellow)
   - `< 50` => `AVOID` (red)
5. Implement hard constraints in two passes:
   - Static eligibility first: maintenance trucks, busy trucks, busy drivers, unavailable/low-baseline-HOS drivers.
   - Route-derived eligibility after the fallback route estimate: pickup infeasible when enough timestamps exist, and driver HOS known to be below estimated required duration.

## Score model details

- `Sprofit = 0.30 * f(margin_pct) + 0.45 * f(deadhead_adjusted_rpm) + 0.25 * f(revenue_per_engine_hour)`, keeping margin important while making deadhead-adjusted yield and engine-hour productivity strong enough to prevent deadhead-heavy loads from hiding behind gross margin.
- `margin_pct` is derived from existing `net_margin / payout`; `deadhead_adjusted_rpm` is existing payout over loaded + deadhead miles; `revenue_per_engine_hour` adds expected dwell from existing facility risk when available.
- `Sdispatch = clamp((Sprofit * Mfacility * Mbroker) - Palerts + Bstrategy, 0, 100)`.
- Score thresholds map to the new public labels: `RECOMMENDED` >= 80, `REVIEW` 50-79, `AVOID` < 50.
- Candidate `rank_score` should become the final dispatch score, while separate metrics expose profitability baseline and modifiers for transparency.

## Files to modify

Likely backend changes:

- `backend/app/services/load_evaluation_service.py`
- `backend/app/schemas/load_evaluation.py`
- `backend/app/services/dispatcher_command_center_service.py`
- `backend/app/schemas/dispatcher_command_center.py`
- `backend/app/services/deadhead.py` if adding a small route-estimate return object/seam around the existing fallback logic
- `backend/app/seed/scenarios.py` for demo expected recommendation labels
- `backend/tests/test_load_evaluation_service.py`
- `backend/tests/services/test_dispatcher_command_center_service.py`
- `backend/tests/routers/test_dispatcher_command_center_api.py`
- `backend/tests/seed/test_mock_loads.py`

Likely frontend changes:

- `frontend/src/types/index.ts`
- `frontend/src/app/dispatcher-command-center/page.tsx`
- `frontend/src/app/dispatcher-command-center/page.test.tsx`
- `frontend/src/app/load-evaluation/page.tsx` for the new `RECOMMENDED` label and profitability terminology
- `frontend/src/components/demo/DemoStoryCard.tsx` and related demo story/test files that still render `TAKE`

## Reuse

Existing code/data to reuse:

- Stored economics: `Load.revenue`, `Load.miles`, `Load.deadhead_miles`, `Load.fuel_cost`, `Load.maintenance_reserve`, `Load.driver_cost`, `Load.tolls` in `backend/app/models/load.py`.
- Existing net margin calculation inputs in `evaluate_load(...)`.
- Existing per-truck deadhead function `truck_deadhead_miles(...)` in `backend/app/services/deadhead.py`.
- Existing average speed fallback `DEFAULT_AVG_SPEED_MPH` in `backend/app/services/load_evaluation_service.py`.
- Existing facility dwell/risk data from `FacilityService.get_facility_risk_by_load_id(...)`.
- Existing broker risk band from `broker_risk_for_load(...)`.
- Existing truck alert severity data from `LiveTruckPosition.highest_alert_severity`.
- Existing origin city match helper `_location_matches_origin(...)`.
- Existing active assignment filtering in `LoadRepository.get_active_assignments_by_fleet(...)`.
- Existing driver HOS filter in `DriverRepository.get_available_by_fleet(...)`.

## Steps

- [ ] Define scoring helpers with bounded continuous scaling, for example `clamp`, `linear_score`, and a small score-breakdown object.
- [ ] Replace threshold-style `operational_score` math in `load_evaluation_service.py` with a continuous `Sprofit` built from existing data:
  - margin contribution derived from `net_margin` and payout/stored costs,
  - deadhead-adjusted RPM using payout / (`loaded_miles + deadhead_miles`),
  - revenue per engine hour using `(loaded_miles + deadhead_miles) / DEFAULT_AVG_SPEED_MPH + expected_dwell_hours`.
- [ ] Extend evaluation inputs/metrics only with derived fields the backend already has or can compute, such as `expected_dwell_hours`, `profitability_score`, and score factors. Keep `operational_score` temporarily as an alias to avoid unnecessary breakage in older consumers during the same PR if desired.
- [ ] Add dispatcher scoring helpers for:
  - `Mfacility`: continuous dwell multiplier using `facility_risk.p90_dwell_hours` when present, falling back to `avg_dwell_hours`/risk band; no penalty when no facility risk exists, but explain that it was unscored.
  - `Mbroker`: existing broker risk band mapping, e.g. low `1.0`, medium `0.95`, high `0.85`.
  - `Palerts`: existing `highest_alert_severity`, e.g. critical `30`, high `20`, medium `10`, low `3`.
  - `Bstrategy`: existing origin-city match and current status/availability bonus only.
- [ ] Refactor `DispatcherCommandCenterService._build_truck_options(...)` into the explicit pipeline:
  - static candidate eligibility filtering,
  - fallback route estimation using existing `truck_deadhead_miles(...)`,
  - route-derived hard filtering for pickup infeasibility and known HOS insufficiency,
  - economics/scoring,
  - risk multipliers and alert penalties,
  - strategic bonuses,
  - final score-to-recommendation mapping.
- [ ] When pickup feasibility cannot be determined because `pickup_time` or `last_seen_at` is missing, do not hard-block the truck; add a reason/factor that timing was incomplete.
- [ ] Add score breakdown fields to dispatcher responses so the UI can explain: profitability baseline, facility multiplier, broker multiplier, alert penalty, strategy bonus, and final dispatch score.
- [ ] Change backend schemas and frontend types from `TAKE` / `MEDIUM_RISK` / `AVOID` to `RECOMMENDED` / `REVIEW` / `AVOID`.
- [ ] Update frontend labels from “Operational Score” to the new profitability/final dispatch terminology without requiring data the backend does not provide.
- [ ] Update tests to assert continuous score behavior, no arbitrary RPM cliffs, hard filtering for maintenance/busy/HOS/pickup infeasibility, risk multiplier behavior, alert penalties, origin-city bonus, and score-band mapping.

## Verification

Backend:

- `cd backend && pytest tests/test_load_evaluation_service.py tests/services/test_dispatcher_command_center_service.py tests/routers/test_dispatcher_command_center_api.py`
- Manually verify seeded demo loads still produce one strong `RECOMMENDED`, one `REVIEW`, and one `AVOID` scenario.

Frontend:

- `cd frontend && npm test -- dispatcher-command-center DemoStoryCard`
- Manually load `/dispatcher-command-center`, select each candidate load, confirm truck rankings, score labels, reasons, and accept flow use `RECOMMENDED` / `REVIEW` / `AVOID` cleanly.

## Decisions

- Public recommendation labels will move to `RECOMMENDED` / `REVIEW` / `AVOID`.
- V1 will stay on the current haversine/stored-deadhead fallback and prepare only a future routing seam; no external routing calls or new provider configuration will be added.
- Pickup infeasibility will become a hard blocker when the backend has enough timing data to determine it.
