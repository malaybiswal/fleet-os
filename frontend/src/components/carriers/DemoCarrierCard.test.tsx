import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DemoCarrierCard } from "./DemoCarrierCard";
import type { CarrierListItem } from "@/types";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Avoid pulling Firebase in via the OutreachActions -> api import chain.
vi.mock("@/lib/api", () => ({
  logContact: vi.fn(),
  updateOutreachStatus: vi.fn(),
}));

afterEach(() => {
  cleanup();
  mockPush.mockClear();
});

const baseCarrier: CarrierListItem = {
  id: 1,
  dot_number: "1234567",
  mc_number: "MC-999999",
  legal_name: "ACME Freight LLC",
  dba_name: "ACME",
  phone: "5551234567",
  email: null,
  address_line1: null,
  city: "Dallas",
  state: "TX",
  postal_code: null,
  country: "US",
  authority_status: "active",
  authority_date: new Date(Date.now() - 30 * 86_400_000).toISOString(),
  power_units: 10,
  driver_count: 8,
  cargo_types: ["general_freight"],
  lead_score: 72,
  outreach_status: "not_contacted",
  contact_attempts: 0,
  last_contacted_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("DemoCarrierCard", () => {
  it("renders company name, location, and fleet size", () => {
    render(<DemoCarrierCard carrier={baseCarrier} />);
    expect(screen.getByText("ACME Freight LLC")).toBeTruthy();
    expect(screen.getByText("Dallas, TX")).toBeTruthy();
    expect(screen.getByText("10 trucks")).toBeTruthy();
  });

  it("shows curated signal badges", () => {
    render(<DemoCarrierCard carrier={baseCarrier} />);
    expect(screen.getByText("New Authority")).toBeTruthy();
    expect(screen.getByText("Growing")).toBeTruthy();
    expect(screen.getByText("Hot Prospect")).toBeTruthy();
  });

  it("hides raw technical DB fields (DOT, MC, raw lead score)", () => {
    render(<DemoCarrierCard carrier={baseCarrier} />);
    expect(screen.queryByText(baseCarrier.dot_number)).toBeNull();
    expect(screen.queryByText(baseCarrier.mc_number!)).toBeNull();
    expect(screen.queryByText("72")).toBeNull();
  });
});
