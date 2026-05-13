import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import AlertsTable from "./AlertsTable";
afterEach(() => {
  cleanup();
});

const alerts = [
  {
    id: 1,
    truck_id: "TRUCK-001",
    severity: "high",
    alert_type: "engine_overheat",
    message: "Engine overheating",
    resolved: false,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    truck_id: "TRUCK-002",
    severity: "low",
    alert_type: "low_fuel",
    message: "Low fuel",
    resolved: true,
    created_at: new Date().toISOString(),
  },
];

describe("AlertsTable", () => {
  it("renders alert rows", () => {
    render(<AlertsTable alerts={alerts} onResolve={vi.fn()} />);

    expect(screen.getByText("TRUCK-001")).toBeTruthy();
    expect(screen.getByText("TRUCK-002")).toBeTruthy();
    expect(screen.getByText("Engine overheating")).toBeTruthy();
  });

  it("calls onResolve when resolve button is clicked", () => {
    const onResolve = vi.fn();

    render(<AlertsTable alerts={alerts} onResolve={onResolve} />);

    fireEvent.click(screen.getAllByText("Resolve")[0]);

    expect(onResolve).toHaveBeenCalledWith(1);
  });
});