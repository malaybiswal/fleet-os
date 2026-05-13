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

import BrokerBarChart from "./BrokerBarChart";

const data = [
  { broker_name: "J.B. Hunt", avg_dwell_hours: 5.1, avg_loading_delay_hours: 0.8, total_detention_pay: "300.00", load_count: 10 },
  { broker_name: "Echo",      avg_dwell_hours: 3.2, avg_loading_delay_hours: 0.3, total_detention_pay: "150.00", load_count: 6  },
];

describe("BrokerBarChart", () => {
  it("renders the heading", () => {
    render(<BrokerBarChart data={data} />);
    expect(screen.getByText("Average Dwell by Broker")).toBeTruthy();
  });

  it("renders with empty data", () => {
    render(<BrokerBarChart data={[]} />);
    expect(screen.getByText("Average Dwell by Broker")).toBeTruthy();
  });
});
