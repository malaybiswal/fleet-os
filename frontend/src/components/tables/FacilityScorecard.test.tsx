import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import FacilityScorecard from "./FacilityScorecard";

const data = [
  {
    facility_name: "Kroger DC",
    avg_dwell_hours: 5.88,
    avg_loading_delay_hours: 0,
    total_detention_pay: "1858.10",
    visit_count: 7,
    facility_score: 41.1,
  },
  {
    facility_name: "Costco DC",
    avg_dwell_hours: 4.33,
    avg_loading_delay_hours: 0,
    total_detention_pay: "1456.79",
    visit_count: 7,
    facility_score: 56.7,
  },
];

describe("FacilityScorecard", () => {
  it("renders facility scorecard rows", () => {
    render(<FacilityScorecard data={data} />);

    expect(screen.getByText("Facility Scorecard")).toBeTruthy();
    expect(screen.getByText("Kroger DC")).toBeTruthy();
    expect(screen.getByText("Costco DC")).toBeTruthy();
    expect(screen.getByText("$1858.10")).toBeTruthy();
    expect(screen.getByText("5.88 hrs")).toBeTruthy();
  });

  it("sorts by score when clicking score header", () => {
    render(<FacilityScorecard data={data} />);

    const scoreHeaders = screen.getAllByText(/Score/);

    fireEvent.click(scoreHeaders[1]);

    const rows = screen.getAllByRole("row");

    expect(rows[1].textContent).toContain("Costco DC");
    expect(rows[2].textContent).toContain("Kroger DC");
  });
});