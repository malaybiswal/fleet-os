import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
}));

import { DwellChart } from "./DwellChart";

describe("DwellChart", () => {
  it("renders heading", () => {
    render(<DwellChart />);
    expect(screen.getByText("Worst Facilities by Dwell Time")).toBeTruthy();
  });
});
