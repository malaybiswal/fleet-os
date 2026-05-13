import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";

afterEach(() => cleanup());

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  PieChart: ({ children }: any) => <div>{children}</div>,
  Pie: () => null,
  Cell: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

import { TruckStatusPie } from "./TruckStatusPie";

const trucks = [
  { truck_id: "T-1", status: "active",      current_location: null, last_seen_at: null, current_lat: null, current_lon: null },
  { truck_id: "T-2", status: "active",      current_location: null, last_seen_at: null, current_lat: null, current_lon: null },
  { truck_id: "T-3", status: "maintenance", current_location: null, last_seen_at: null, current_lat: null, current_lon: null },
];

describe("TruckStatusPie", () => {
  it("renders heading", () => {
    render(<TruckStatusPie trucks={trucks} />);
    expect(screen.getByText("Truck Status Mix")).toBeTruthy();
  });

  it("renders empty state when no trucks", () => {
    render(<TruckStatusPie trucks={[]} />);
    expect(screen.getByText("No truck data available.")).toBeTruthy();
  });
});
