# Dispatcher Command Center System Flaws

This document tracks product, data-model, and implementation flaws discovered in the Dispatcher Command Center feature.

## Flaws

### 1. Load evaluation concept conflicts with current load assignment model

**Issue:** The Command Center is framed as answering: “Given this load, should we take it, and which truck should cover it?” However, the current `loads` model requires `truck_id` and `driver_id`, meaning loads are already assigned before they appear in the Command Center.

**Why this is a problem:** A true pre-booking/load-opportunity workflow should evaluate unassigned candidate loads. If a load already has a truck and driver, then the system is no longer deciding whether to take the load from scratch; it is evaluating an already-booked/assigned load.

**Current behavior:**
- `truck_id` and `driver_id` are required on `Load`.
- Demo loads are seeded with preassigned truck/driver IDs.
- `POST /api/loads` requires truck/driver IDs.
- The Command Center ranks trucks anyway, using the existing `load.truck_id` only as a small deterministic tie-breaker.

**Potential fix:** Separate candidate load opportunities from booked/assigned loads, or make `truck_id` and `driver_id` nullable until a dispatch decision is accepted.

### 2. Deadhead distance does not account for legal truck routing

**Issue:** The Command Center currently estimates deadhead distance with either straight-line haversine distance between truck coordinates and load origin coordinates, or a stored `deadhead_miles` fallback.

**Why this is a problem:** This does not represent the distance or time along routes a commercial truck can legally take. It ignores road network distance, truck restrictions, bridge/tunnel limits, hazmat constraints, height/weight limits, tolls, closures, weather, traffic, and exact facility access.

**Current behavior:**
- `truck_deadhead_miles(...)` returns haversine distance when coordinates are available.
- If coordinates are missing, it falls back to the load's stored `deadhead_miles`.
- Pickup feasibility then estimates ETA as `deadhead_miles / DEFAULT_AVG_SPEED_MPH`.

**Potential fix:** Integrate a truck-routing provider, such as Trimble Maps/PC*MILER, HERE Truck Routing, Mapbox, or another routing engine that supports commercial vehicle constraints. Deadhead should return route distance, route duration, legal-route status, tolls, and restriction details. Pickup feasibility should use routed duration instead of average-speed mileage.

## Open Questions

- Should the Command Center evaluate unassigned load opportunities or already-booked loads?
- Should “take/avoid” exist only before booking?
- Should truck assignment happen inside the Command Center?
- Should accepting a recommendation update the load’s assigned truck/driver?

## Notes

Add new flaws below this section as they are discovered.
