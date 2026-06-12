import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import LoadsTable from "./LoadsTable";
afterEach(() => {
  cleanup();
});

const loads = [
  {
    id: 1,
    load_id: "LOAD-TEST-001",
    truck_id: "TRUCK-001",
    driver_id: "DRIVER-001",
    broker_name: "Test Broker",
    origin: "Austin, TX",
    destination: "Dallas, TX",
    revenue: "2500.00",
    miles: "210.00",
    deadhead_miles: "25.00",
    fuel_cost: "450.00",
    maintenance_reserve: "100.00",
    driver_cost: "700.00",
    tolls: "50.00",
    status: "booked",
    pickup_time: "2026-05-14T10:00:00Z",
    delivery_time: "2026-05-14T18:00:00Z",
  },
];

describe("LoadsTable", () => {
  it("renders load rows", () => {
    render(<LoadsTable loads={loads} />);

    expect(screen.getByText("LOAD-TEST-001")).toBeTruthy();
    expect(screen.getByText("Test Broker")).toBeTruthy();
    expect(screen.getByText("Austin, TX")).toBeTruthy();
    expect(screen.getByText("Dallas, TX")).toBeTruthy();
    expect(screen.getByText("$2500.00")).toBeTruthy();
  });

  it("calculates RPM, deadhead percentage, and net profit", () => {
    render(<LoadsTable loads={loads} />);

    expect(screen.getByText("$11.90")).toBeTruthy();
    expect(screen.getByText("11.9%")).toBeTruthy();
    expect(screen.getByText("$1200.00")).toBeTruthy();
  });
});

it("renders pickup and delivery timestamps", () => {
  render(<LoadsTable loads={loads} />);

  expect(screen.getByText("Pickup")).toBeTruthy();
  expect(screen.getByText("Delivery")).toBeTruthy();

  expect(
    screen.getAllByText((content) => content.includes("2026")).length
  ).toBeGreaterThan(0);
});

describe("LoadsTable facility risk", () => {
  it("renders 'No data' when a load has no facility risk", () => {
    render(<LoadsTable loads={loads} />);

    expect(screen.getByText("No data")).toBeTruthy();
  });

  it("renders the facility risk band when present", () => {
    const loadsWithRisk = [
      {
        ...loads[0],
        facility_risk: {
          facility_id: 1,
          facility_name: "Dallas Mega Cold Storage",
          operational_score: 11,
          avg_dwell_hours: 8.5,
          p90_dwell_hours: 12,
          appointment_reliability_pct: 40,
          detention_risk_score: 80,
          detention_risk_band: "high" as const,
          visit_count: 5,
          confidence: "medium" as const,
        },
      },
    ];

    render(<LoadsTable loads={loadsWithRisk} />);

    expect(screen.getByText("High Risk")).toBeTruthy();
  });
});