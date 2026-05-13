import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

import { RevenueChart } from "./RevenueChart";

describe("RevenueChart", () => {
  it("renders heading", () => {
    render(<RevenueChart />);
    expect(screen.getByText("Weekly Revenue & Profit")).toBeTruthy();
  });
});
