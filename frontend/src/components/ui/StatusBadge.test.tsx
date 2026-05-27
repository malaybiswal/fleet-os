import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import StatusBadge from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders delivered status", () => {
    render(<StatusBadge status="delivered" />);

    expect(screen.getByText("delivered")).toBeTruthy();
  });

  it("renders in transit status with readable label", () => {
    render(<StatusBadge status="in_transit" />);

    expect(screen.getByText("in transit")).toBeTruthy();
  });

  it("renders canonical truck operational statuses", () => {
    render(<StatusBadge status="moving" />);

    expect(screen.getByText("moving")).toBeTruthy();
  });
});
