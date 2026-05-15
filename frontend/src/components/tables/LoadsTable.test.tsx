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