import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";

afterEach(() => cleanup());

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

import { Topbar } from "./Topbar";

describe("Topbar", () => {
  it("renders the Dashboard title on root path", () => {
    render(<Topbar />);
    expect(screen.getByText("Dashboard")).toBeTruthy();
  });

  it("renders the Live indicator", () => {
    render(<Topbar />);
    expect(screen.getByText("Live")).toBeTruthy();
  });
});
