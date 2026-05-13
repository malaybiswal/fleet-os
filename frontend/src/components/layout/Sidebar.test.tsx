import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";

afterEach(() => cleanup());

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  it("renders the brand name", () => {
    render(<Sidebar />);
    expect(screen.getByText("Fleet OS")).toBeTruthy();
  });

  it("renders all nav items", () => {
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeTruthy();
    expect(screen.getByText("Dwell")).toBeTruthy();
    expect(screen.getByText("Trucks")).toBeTruthy();
    expect(screen.getByText("Alerts")).toBeTruthy();
  });

  it("marks Dashboard as active on root path", () => {
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink?.className).toContain("bg-zinc-800");
  });
});
