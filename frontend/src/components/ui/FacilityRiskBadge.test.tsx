import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import FacilityRiskBadge from "./FacilityRiskBadge";
import type { FacilityRiskSummary } from "@/types";

const baseRisk: FacilityRiskSummary = {
  facility_id: 1,
  facility_name: "Dallas Mega Cold Storage",
  operational_score: 11,
  avg_dwell_hours: 8.5,
  p90_dwell_hours: 12,
  appointment_reliability_pct: 40,
  detention_risk_score: 80,
  detention_risk_band: "high",
  visit_count: 5,
  confidence: "medium",
};

describe("FacilityRiskBadge", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders 'No data' when facility risk is null", () => {
    render(<FacilityRiskBadge facilityRisk={null} />);

    expect(screen.getByText("No data")).toBeTruthy();
  });

  it("renders 'No data' when detention risk band is null", () => {
    render(
      <FacilityRiskBadge
        facilityRisk={{ ...baseRisk, detention_risk_band: null }}
      />,
    );

    expect(screen.getByText("No data")).toBeTruthy();
  });

  it("renders high risk badge with tooltip details", () => {
    render(<FacilityRiskBadge facilityRisk={baseRisk} />);

    expect(screen.getByText("High Risk")).toBeTruthy();
    expect(screen.getByText("Dallas Mega Cold Storage")).toBeTruthy();
    expect(screen.getByText(/Operational score: 11\/100/)).toBeTruthy();
    expect(screen.getByText(/8.5h avg \/ 12.0h worst-case/)).toBeTruthy();
    expect(screen.getByText(/Appointment reliability: 40%/)).toBeTruthy();
    expect(screen.getByText(/Detention risk score: 80\/100/)).toBeTruthy();
    expect(screen.getByText(/Based on 5 visits \(medium confidence\)/)).toBeTruthy();
  });

  it("renders low risk badge", () => {
    render(
      <FacilityRiskBadge
        facilityRisk={{ ...baseRisk, detention_risk_band: "low" }}
      />,
    );

    expect(screen.getByText("Low Risk")).toBeTruthy();
  });

  it("renders medium risk badge", () => {
    render(
      <FacilityRiskBadge
        facilityRisk={{ ...baseRisk, detention_risk_band: "medium" }}
      />,
    );

    expect(screen.getByText("Medium Risk")).toBeTruthy();
  });
});
