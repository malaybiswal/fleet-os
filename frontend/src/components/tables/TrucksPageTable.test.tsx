import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import TrucksPageTable from "./TrucksPageTable";

afterEach(() => {
  cleanup();
});

const trucks = [
  {
    id: 1,
    truck_id: "TRUCK-001",
    status: "moving",
    current_location: "Austin, TX",
    current_lat: 30.2672,
    current_lon: -97.7431,
    last_seen_at: "2026-05-15T00:00:00Z",
    created_at: "2026-05-11T03:51:45Z",
  },
  {
    id: 2,
    truck_id: "TRUCK-002",
    status: "maintenance",
    current_location: "Dallas, TX",
    current_lat: null,
    current_lon: null,
    last_seen_at: null,
    created_at: "2026-05-11T03:51:45Z",
  },
];

describe("TrucksPageTable", () => {
  it("renders truck rows", () => {
    render(<TrucksPageTable trucks={trucks} />);

    expect(screen.getByText("TRUCK-001")).toBeTruthy();
    expect(screen.getByText("TRUCK-002")).toBeTruthy();
    expect(screen.getByText("Austin, TX")).toBeTruthy();
    expect(screen.getByText("Dallas, TX")).toBeTruthy();
  });

  it("renders truck statuses", () => {
    render(<TrucksPageTable trucks={trucks} />);

    expect(screen.getByText("moving")).toBeTruthy();
    expect(screen.getByText("maintenance")).toBeTruthy();
  });
});
