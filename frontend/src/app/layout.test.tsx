import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";

afterEach(() => cleanup());

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));
vi.mock("../globals.css", () => ({}));

import RootLayout from "./layout";

describe("RootLayout", () => {
  it("renders children", () => {
    render(<RootLayout><p>hello world</p></RootLayout>);
    expect(screen.getByText("hello world")).toBeTruthy();
  });

  it("renders the sidebar brand", () => {
    render(<RootLayout><span /></RootLayout>);
    expect(screen.getByText("Fleet OS")).toBeTruthy();
  });

  it("renders the topbar Live indicator", () => {
    render(<RootLayout><span /></RootLayout>);
    expect(screen.getByText("Live")).toBeTruthy();
  });
});
