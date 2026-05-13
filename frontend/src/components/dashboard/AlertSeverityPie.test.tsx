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

import { AlertSeverityPie } from "./AlertSeverityPie";

const alerts = [
  { id: 1, truck_id: "T-1", severity: "critical", alert_type: "engine", message: "Engine fault", created_at: "2026-05-12T00:00:00Z", resolved: false },
  { id: 2, truck_id: "T-2", severity: "low",      alert_type: "fuel",   message: "Low fuel",    created_at: "2026-05-12T00:00:00Z", resolved: false },
];

describe("AlertSeverityPie", () => {
  it("renders heading", () => {
    render(<AlertSeverityPie alerts={alerts} />);
    expect(screen.getByText("Alert Severity Mix")).toBeTruthy();
  });

  it("renders empty state when no alerts", () => {
    render(<AlertSeverityPie alerts={[]} />);
    expect(screen.getByText("No open alerts.")).toBeTruthy();
  });
});
