import React from "react";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/components/charts/DwellBarChart",    () => ({ default: () => <div>DwellBarChart</div> }));
vi.mock("@/components/charts/BrokerBarChart",   () => ({ default: () => <div>BrokerBarChart</div> }));
vi.mock("@/components/charts/DetentionChart",   () => ({ default: () => <div>DetentionChart</div> }));
vi.mock("@/components/tables/FacilityScorecard", () => ({ default: () => <div>FacilityScorecard</div> }));

import DwellPage from "./page";

function makeResponse(data: unknown) {
  return Promise.resolve({ json: () => Promise.resolve(data) } as Response);
}

describe("DwellPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((url: string) => {
      if (url.includes("facility-scorecard")) return makeResponse([]);
      if (url.includes("broker-scorecard"))   return makeResponse([]);
      return makeResponse([]);
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows loading state initially", () => {
    render(<DwellPage />);
    expect(screen.getByText(/Loading dwell analytics/)).toBeTruthy();
  });

  it("renders page heading after data loads", async () => {
    render(<DwellPage />);
    await waitFor(() => {
      expect(screen.getByText("Dwell Analytics")).toBeTruthy();
    });
  });

  it("renders child charts after data loads", async () => {
    render(<DwellPage />);
    await waitFor(() => {
      expect(screen.getByText("DwellBarChart")).toBeTruthy();
      expect(screen.getByText("BrokerBarChart")).toBeTruthy();
    });
  });

  it("shows error state when fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));
    render(<DwellPage />);
    await waitFor(() => {
      expect(screen.getByText("Failed to load dwell analytics")).toBeTruthy();
    });
  });
});
