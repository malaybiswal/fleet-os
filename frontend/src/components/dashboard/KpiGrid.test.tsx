import React from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { KpiGrid } from "./KpiGrid";

beforeEach(() => {
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));
});

describe("KpiGrid", () => {
  it("renders KPI labels", () => {
    render(
      <KpiGrid
        summary={{
          active_trucks: 3,
          avg_dwell_hours: 4.7,
          total_revenue: "10000",
          avg_revenue_per_mile: "2.25",
          deadhead_percentage: 12.5,
          open_alerts: 2,
          open_loads: 5,
          fuel_cost_per_mile: "0.65",
        }}
        trucks={[]}
        alerts={[]}
      />
    );

    expect(screen.getByText("Active Trucks")).toBeTruthy();
    expect(screen.getByText("Open Alerts")).toBeTruthy();
    expect(screen.getByText("Total Revenue")).toBeTruthy();
    expect(screen.getByText("Avg Rev / Mile")).toBeTruthy();
  });
});
