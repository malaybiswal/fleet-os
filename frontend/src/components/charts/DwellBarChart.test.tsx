import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";

afterEach(() => cleanup());

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

import DwellBarChart from "./DwellBarChart";

const data = [
  { facility_name: "Walmart DC", avg_dwell_hours: 7.2, avg_loading_delay_hours: 1.0, total_detention_pay: "400.00", visit_count: 5, facility_score: 30.0 },
  { facility_name: "Kroger",     avg_dwell_hours: 4.8, avg_loading_delay_hours: 0.5, total_detention_pay: "200.00", visit_count: 3, facility_score: 55.0 },
];

describe("DwellBarChart", () => {
  it("renders the heading", () => {
    render(<DwellBarChart data={data} />);
    expect(screen.getByText("Top Worst Facilities by Dwell Time")).toBeTruthy();
  });

  it("renders with empty data", () => {
    render(<DwellBarChart data={[]} />);
    expect(screen.getByText("Top Worst Facilities by Dwell Time")).toBeTruthy();
  });
});
