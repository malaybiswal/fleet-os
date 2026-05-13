import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, afterEach } from "vitest";

afterEach(() => cleanup());

import { TruckTable } from "./TruckTable";

const trucks = [
  {
    truck_id: "TRUCK-001",
    status: "active",
    current_location: "Austin, TX",
    last_seen_at: "2026-05-12T10:00:00Z",
    current_lat: null,
    current_lon: null,
  },
  {
    truck_id: "TRUCK-002",
    status: "idle",
    current_location: null,
    last_seen_at: null,
    current_lat: null,
    current_lon: null,
  },
];

describe("TruckTable", () => {
  it("renders empty state", () => {
    render(<TruckTable trucks={[]} />);
    expect(screen.getByText("No trucks available.")).toBeTruthy();
  });

  it("renders truck rows", () => {
    render(<TruckTable trucks={trucks} />);
    expect(screen.getByText("TRUCK-001")).toBeTruthy();
    expect(screen.getByText("TRUCK-002")).toBeTruthy();
    expect(screen.getByText("Austin, TX")).toBeTruthy();
  });

  it("shows Unknown for missing location", () => {
    render(<TruckTable trucks={trucks} />);
    expect(screen.getByText("Unknown")).toBeTruthy();
  });

  it("shows N/A for missing last_seen_at", () => {
    render(<TruckTable trucks={trucks} />);
    expect(screen.getByText("N/A")).toBeTruthy();
  });
});
