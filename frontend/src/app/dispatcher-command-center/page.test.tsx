import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DispatcherCommandCenterPage from "./page";
import type { DispatcherCommandCenterDecision, Load } from "@/types";

const apiMocks = vi.hoisted(() => ({
  getDispatcherDecision: vi.fn(),
  getDispatcherCandidates: vi.fn(),
  acceptDispatcherRecommendation: vi.fn(),
}));

const authMocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
}));

vi.mock("@/lib/api", () => apiMocks);

vi.mock("@/components/auth/AuthProvider", () => ({
  useAuth: authMocks.useAuth,
}));

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  vi.clearAllMocks();
  authMocks.useAuth.mockReturnValue({
    isAuthenticated: true,
    isLoading: false,
  });
  apiMocks.getDispatcherCandidates.mockResolvedValue(loads);
  apiMocks.getDispatcherDecision.mockResolvedValue(decision);
  apiMocks.acceptDispatcherRecommendation.mockResolvedValue({
    ...loads[0],
    truck_id: "TRUCK-001",
    driver_id: "DRIVER-001",
    status: "booked",
  });
});

const loads: Load[] = [
  {
    id: 1,
    load_id: "LOAD-GOOD",
    truck_id: "TRUCK-001",
    driver_id: "DRIVER-001",
    broker_name: "CH Robinson",
    origin: "Dallas, TX",
    destination: "Houston, TX",
    revenue: "950.00",
    miles: "260.00",
    deadhead_miles: "20.00",
    status: "booked",
    facility_risk: {
      facility_id: 1,
      facility_name: "Houston Crossdock",
      operational_score: 92,
      avg_dwell_hours: 1.2,
      p90_dwell_hours: 1.4,
      appointment_reliability_pct: 100,
      detention_risk_score: 5,
      detention_risk_band: "low",
      visit_count: 4,
      confidence: "medium",
    },
  },
  {
    id: 2,
    load_id: "LOAD-RISK",
    truck_id: "TRUCK-002",
    driver_id: "DRIVER-002",
    broker_name: "Cold Chain Logistics",
    origin: "Fort Worth, TX",
    destination: "Memphis, TN",
    revenue: "2400.00",
    miles: "850.00",
    deadhead_miles: "90.00",
    status: "in_transit",
  },
];

const scoreBreakdown = {
  profitability_baseline: 88,
  facility_multiplier: 1,
  broker_multiplier: 1,
  alert_penalty: 0,
  strategy_bonus: 20,
  final_dispatch_score: 108,
};

const decision: DispatcherCommandCenterDecision = {
  load: loads[0],
  final_recommendation: "REVIEW",
  facility_risk: loads[0].facility_risk ?? null,
  best_truck: {
    truck_id: "TRUCK-001",
    driver_id: "DRIVER-001",
    driver_name: "Maria Lopez",
    driver_hos_hours_remaining: 8,
    status: "moving",
    current_location: "Dallas yard",
    latitude: 32.7767,
    longitude: -96.797,
    last_seen_at: "2026-06-01T12:00:00Z",
    active_alert_count: 0,
    highest_alert_severity: null,
    recommendation: "REVIEW",
    rank_score: 108,
    deadhead_miles: 20,
    deadhead_source: "haversine",
    can_make_pickup: true,
    estimated_revenue_per_hour: 186.27,
    operational_score: 88,
    profitability_score: 88,
    score_breakdown: scoreBreakdown,
    reasons: ["Strong deadhead-adjusted RPM"],
    ranking_factors: ["Current location matches the load origin city"],
  },
  truck_options: [
    {
      truck_id: "TRUCK-001",
      driver_id: "DRIVER-001",
      driver_name: "Maria Lopez",
      driver_hos_hours_remaining: 8,
      status: "moving",
      current_location: "Dallas yard",
      latitude: 32.7767,
      longitude: -96.797,
      last_seen_at: "2026-06-01T12:00:00Z",
      active_alert_count: 0,
      highest_alert_severity: null,
      recommendation: "REVIEW",
      rank_score: 108,
      deadhead_miles: 20,
      deadhead_source: "haversine",
      can_make_pickup: true,
      estimated_revenue_per_hour: 186.27,
      operational_score: 88,
      profitability_score: 88,
      score_breakdown: scoreBreakdown,
      reasons: ["Strong deadhead-adjusted RPM"],
      ranking_factors: ["Current location matches the load origin city"],
    },
    {
      truck_id: "TRUCK-002",
      driver_id: "DRIVER-002",
      driver_name: "Jordan Smith",
      driver_hos_hours_remaining: 6.5,
      status: "idle",
      current_location: "Fort Worth staging",
      latitude: 32.7555,
      longitude: -97.3308,
      last_seen_at: "2026-06-01T12:05:00Z",
      active_alert_count: 1,
      highest_alert_severity: "high",
      recommendation: "REVIEW",
      rank_score: 70,
      deadhead_miles: 84,
      deadhead_source: "stored-fallback",
      can_make_pickup: false,
      estimated_revenue_per_hour: 186.27,
      operational_score: 88,
      profitability_score: 88,
      score_breakdown: scoreBreakdown,
      reasons: ["Strong deadhead-adjusted RPM"],
      ranking_factors: ["Unresolved alert risk applies -18"],
    },
  ],
  metrics: {
    gross_rpm: 3.65,
    deadhead_adjusted_rpm: 3.39,
    estimated_fuel_cost: 160,
    estimated_revenue_per_hour: 186.27,
    deadhead_penalty: 7.1,
    estimated_drive_hours: 5.09,
    profitability_score: 88,
    operational_score: 88,
    profitability_factors: {
      margin_score: 90,
      net_rpm_score: 95,
      revenue_per_hour_score: 80,
    },
    net_margin: 565,
    stored_costs_used: true,
    deadhead_miles: 20,
    broker_risk_band: "low",
    expected_dwell_hours: 1.2,
    facility_detention_risk_band: "low",
    profitability_baseline: 88,
    facility_multiplier: 1,
    broker_multiplier: 1,
    alert_penalty: 0,
    strategy_bonus: 20,
    final_dispatch_score: 108,
  },
  reasons: [
    "Strong deadhead-adjusted RPM",
    "Low dwell risk at Houston Crossdock supports the plan",
  ],
  decision_notes: ["Stage 1 uses a demo-safe deadhead model."],
  is_candidate: true,
};

describe("DispatcherCommandCenterPage", () => {
  it("renders loads and fetches a decision when a load is selected", async () => {
    render(<DispatcherCommandCenterPage />);

    expect(await screen.findByText("LOAD-GOOD")).toBeTruthy();
    expect(screen.getByText("LOAD-RISK")).toBeTruthy();

    fireEvent.click(screen.getByText("LOAD-GOOD").closest("button")!);

    await waitFor(() => {
      expect(apiMocks.getDispatcherDecision).toHaveBeenCalledWith("LOAD-GOOD");
    });

    expect(await screen.findByText("REVIEW")).toBeTruthy();
    expect(screen.queryByText("MEDIUM RISK")).toBeNull();
    expect(screen.getByText("Best truck: TRUCK-001 with Maria Lopez")).toBeTruthy();
    expect(screen.getByText("Selected Load")).toBeTruthy();
    expect(screen.getAllByText("Broker: CH Robinson").length).toBeGreaterThan(0);
    expect(screen.getByText("LOW broker risk")).toBeTruthy();
    expect(screen.getAllByText("Revenue: $950.00").length).toBeGreaterThan(0);
    expect(screen.getByText("$186.27")).toBeTruthy();
    expect(screen.getByText("$565.00")).toBeTruthy();
    expect(screen.getAllByText("20 mi").length).toBeGreaterThan(0);
    expect(screen.getByText("88/100")).toBeTruthy();
    expect(screen.getByText("Strong deadhead-adjusted RPM")).toBeTruthy();
    expect(screen.getAllByText("Houston Crossdock").length).toBeGreaterThan(0);
  });

  it("renders ranked truck alternatives in response order", async () => {
    render(<DispatcherCommandCenterPage />);

    fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);
    await screen.findByText("Ranked Truck Options");

    const rows = screen.getAllByRole("row").map((row) => row.textContent ?? "");

    expect(rows[1]).toContain("TRUCK-001");
    expect(rows[1]).toContain("Maria Lopez");
    expect(rows[1]).toContain("Makes pickup");
    expect(rows[1]).toContain("View details");
    expect(rows[1]).not.toContain("8.0h");
    expect(rows[1]).not.toContain("20 mi");
    expect(rows[2]).toContain("TRUCK-002");
    expect(rows[2]).toContain("Jordan Smith");
    expect(rows[2]).toContain("Misses pickup");

    fireEvent.click(screen.getByText("TRUCK-002").closest("tr")!);

    expect(screen.getByText("HOS remaining")).toBeTruthy();
    expect(screen.getByText("6.5h")).toBeTruthy();
    expect(screen.getByText("84 mi")).toBeTruthy();
    expect(screen.getByText("stored-fallback")).toBeTruthy();
    expect(screen.getByText("Unresolved alert risk applies -18")).toBeTruthy();
  });

  it("puts demo showcase candidate loads first in order", async () => {
    apiMocks.getDispatcherCandidates.mockResolvedValue([
      demoLoad("DEMO-CAND-BAD-DEADHEAD", "Amarillo, TX", "Oklahoma City, OK"),
      demoLoad("LOAD-NORMAL", "Waco, TX", "Tulsa, OK"),
      demoLoad("DEMO-CAND-WEAK-BROKER", "El Paso, TX", "Phoenix, AZ"),
      demoLoad("DEMO-CAND-GOOD", "Dallas, TX", "Houston, TX"),
    ]);

    render(<DispatcherCommandCenterPage />);

    expect(await screen.findByText("DEMO-CAND-GOOD")).toBeTruthy();

    const loadButtons = screen
      .getAllByRole("button")
      .map((button) => button.textContent ?? "");

    expect(loadButtons[0]).toContain("DEMO-CAND-GOOD");
    expect(loadButtons[1]).toContain("DEMO-CAND-WEAK-BROKER");
    expect(loadButtons[2]).toContain("DEMO-CAND-BAD-DEADHEAD");
    expect(loadButtons[3]).toContain("LOAD-NORMAL");
  });

  it("renders empty loads state", async () => {
    apiMocks.getDispatcherCandidates.mockResolvedValue([]);

    render(<DispatcherCommandCenterPage />);

    expect(
      await screen.findByText("No loads are available for command-center evaluation."),
    ).toBeTruthy();
  });

  it("renders load and decision loading states", async () => {
    const pendingDecision = deferred<DispatcherCommandCenterDecision>();
    apiMocks.getDispatcherDecision.mockReturnValue(pendingDecision.promise);

    render(<DispatcherCommandCenterPage />);

    expect(await screen.findByText("LOAD-GOOD")).toBeTruthy();
    fireEvent.click(screen.getByText("LOAD-GOOD").closest("button")!);

    expect(await screen.findByText("Loading dispatcher decision...")).toBeTruthy();

    pendingDecision.resolve(decision);
    expect(await screen.findByText("Best truck: TRUCK-001 with Maria Lopez")).toBeTruthy();
  });

  it("renders API error states", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    try {
      apiMocks.getDispatcherDecision.mockRejectedValue(new Error("Nope"));

      render(<DispatcherCommandCenterPage />);

      fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);

      expect(await screen.findByText("Failed to load dispatcher decision.")).toBeTruthy();
    } finally {
      consoleError.mockRestore();
    }
  });

  it("renders readable validation errors from the API", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    try {
      apiMocks.getDispatcherDecision.mockRejectedValue({
        status: 422,
        message: "Load revenue must be greater than 0",
      });

      render(<DispatcherCommandCenterPage />);

      fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);

      expect(
        await screen.findByText("Load revenue must be greater than 0"),
      ).toBeTruthy();
      expect(screen.queryByText("Failed to load dispatcher decision.")).toBeNull();
    } finally {
      consoleError.mockRestore();
    }
  });

  it("renders no eligible truck decisions cleanly", async () => {
    apiMocks.getDispatcherDecision.mockResolvedValue({
      ...decision,
      final_recommendation: "AVOID",
      best_truck: null,
      truck_options: [],
      reasons: ["No eligible trucks are available for this load"],
    });

    render(<DispatcherCommandCenterPage />);

    fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);

    expect(
      await screen.findByText("No eligible truck is available for this load."),
    ).toBeTruthy();
    expect(screen.getByText("No eligible truck options were returned.")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Accept recommendation" }).hasAttribute("disabled"),
    ).toBe(true);
  });

  it("accepts the best recommendation and refreshes candidate loads", async () => {
    apiMocks.getDispatcherCandidates
      .mockResolvedValueOnce(loads)
      .mockResolvedValueOnce([loads[1]]);

    render(<DispatcherCommandCenterPage />);

    fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);
    await screen.findByText("Best truck: TRUCK-001 with Maria Lopez");

    fireEvent.click(screen.getByRole("button", { name: "Accept recommendation" }));

    await waitFor(() => {
      expect(apiMocks.acceptDispatcherRecommendation).toHaveBeenCalledWith(
        "LOAD-GOOD",
        "TRUCK-001",
        "DRIVER-001",
      );
    });
    expect(apiMocks.getDispatcherCandidates).toHaveBeenCalledTimes(2);
    expect(
      await screen.findByText("Booked LOAD-GOOD to TRUCK-001 with DRIVER-001."),
    ).toBeTruthy();
    expect(screen.queryByText("Best truck: TRUCK-001 with Maria Lopez")).toBeNull();
  });

  it("renders readable accept conflicts from the API", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    try {
      apiMocks.acceptDispatcherRecommendation.mockRejectedValue({
        status: 409,
        message: "Load LOAD-GOOD is already booked or no longer available",
      });

      render(<DispatcherCommandCenterPage />);

      fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);
      await screen.findByText("Best truck: TRUCK-001 with Maria Lopez");

      fireEvent.click(screen.getByRole("button", { name: "Accept recommendation" }));

      expect(
        await screen.findByText("Load LOAD-GOOD is already booked or no longer available"),
      ).toBeTruthy();
      expect(screen.queryByText("Failed to accept recommendation.")).toBeNull();
    } finally {
      consoleError.mockRestore();
    }
  });

  it("disables accept for non-candidate review decisions", async () => {
    apiMocks.getDispatcherDecision.mockResolvedValue({
      ...decision,
      is_candidate: false,
    });

    render(<DispatcherCommandCenterPage />);

    fireEvent.click((await screen.findByText("LOAD-GOOD")).closest("button")!);

    expect(await screen.findByText("Best truck: TRUCK-001 with Maria Lopez")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Accept recommendation" }).hasAttribute("disabled"),
    ).toBe(true);
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, resolve, reject };
}

function demoLoad(loadId: string, origin: string, destination: string): Load {
  return {
    ...loads[0],
    id: loadId
      .split("")
      .reduce((total, character) => total + character.charCodeAt(0), 0),
    load_id: loadId,
    origin,
    destination,
  };
}
