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

import DetentionChart from "./DetentionChart";

const data = [
  { facility_name: "Sysco", avg_dwell_hours: 6.1, avg_loading_delay_hours: 1.2, total_detention_pay: "980.50", visit_count: 8, facility_score: 25.0 },
  { facility_name: "HEB DC", avg_dwell_hours: 2.1, avg_loading_delay_hours: 0.2, total_detention_pay: "120.00", visit_count: 4, facility_score: 78.0 },
];

describe("DetentionChart", () => {
  it("renders the heading", () => {
    render(<DetentionChart data={data} />);
    expect(screen.getByText("Detention Pay by Facility")).toBeTruthy();
  });

  it("renders with empty data", () => {
    render(<DetentionChart data={[]} />);
    expect(screen.getByText("Detention Pay by Facility")).toBeTruthy();
  });
});
