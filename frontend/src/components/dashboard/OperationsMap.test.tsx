import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OperationsMap } from "./OperationsMap";

const makeTruck = (id: number, lat?: string, lon?: string) => ({
  id,
  truck_id: `TRK-${id}`,
  status: "active",
  current_location: null,
  current_lat: lat ?? null,
  current_lon: lon ?? null,
  last_seen_at: null,
  created_at: "2026-01-01T00:00:00Z",
});

describe("OperationsMap", () => {
  it("counts trucks with GPS coordinates", () => {
    const trucks = [
      makeTruck(1, "30.26", "-97.74"),
      makeTruck(2, "29.76", "-95.37"),
      makeTruck(3),
    ];
    render(<OperationsMap trucks={trucks} />);
    expect(screen.getByText(/2 trucks have GPS coordinates/)).toBeTruthy();
  });

  it("shows 0 when no trucks have GPS", () => {
    render(<OperationsMap trucks={[makeTruck(1)]} />);
    expect(screen.getByText(/0 trucks have GPS coordinates/)).toBeTruthy();
  });
});
