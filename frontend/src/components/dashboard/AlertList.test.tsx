import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AlertList } from "./AlertList";

describe("AlertList", () => {
  it("renders empty state", () => {
    render(<AlertList alerts={[]} />);

    expect(screen.getByText("No open alerts.")).toBeTruthy();
  });

  it("renders alerts", () => {
    render(
      <AlertList
        alerts={[
          {
            id: 1,
            truck_id: "TRUCK-001",
            severity: "medium",
            alert_type: "low_fuel",
            message: "Fuel is low",
            created_at: "2026-05-10T00:00:00Z",
            resolved: false,
          },
        ]}
      />
    );

    expect(screen.getByText("low_fuel")).toBeTruthy();
    expect(screen.getByText("Fuel is low")).toBeTruthy();
  });
});