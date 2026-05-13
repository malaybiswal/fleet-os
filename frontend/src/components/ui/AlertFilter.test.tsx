import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AlertFilter from "./AlertFilter";

describe("AlertFilter", () => {
  it("renders severity dropdown", () => {
    render(<AlertFilter value="all" onChange={vi.fn()} />);

    expect(screen.getByText(/Severity/i)).toBeTruthy();
  });
});