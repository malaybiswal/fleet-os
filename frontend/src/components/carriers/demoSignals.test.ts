import { describe, expect, it } from "vitest";

import type { CarrierListItem } from "@/types";
import {
  formatFleetSize,
  isGrowthFleet,
  isNewAuthority,
  prospectTier,
} from "./demoSignals";

function makeCarrier(overrides: Partial<CarrierListItem> = {}): CarrierListItem {
  return {
    id: 1,
    dot_number: "1234567",
    mc_number: "MC-123",
    legal_name: "Acme Trucking",
    dba_name: null,
    phone: "5551234567",
    email: null,
    address_line1: null,
    city: "Dallas",
    state: "TX",
    postal_code: null,
    country: "US",
    authority_status: "active",
    authority_date: null,
    power_units: null,
    driver_count: null,
    cargo_types: null,
    lead_score: null,
    outreach_status: "not_contacted",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function daysAgo(days: number): string {
  return new Date(Date.now() - days * 86_400_000).toISOString();
}

describe("isNewAuthority", () => {
  it("is true for authority granted within the last 365 days", () => {
    expect(isNewAuthority(makeCarrier({ authority_date: daysAgo(30) }))).toBe(true);
    expect(isNewAuthority(makeCarrier({ authority_date: daysAgo(365) }))).toBe(true);
  });

  it("is false for authority older than 365 days", () => {
    expect(isNewAuthority(makeCarrier({ authority_date: daysAgo(366) }))).toBe(false);
  });

  it("is false when authority_date is missing", () => {
    expect(isNewAuthority(makeCarrier({ authority_date: null }))).toBe(false);
  });
});

describe("isGrowthFleet", () => {
  it("is false below the growth band", () => {
    expect(isGrowthFleet(makeCarrier({ power_units: 4 }))).toBe(false);
  });

  it("is true at the edges of the 5-25 band", () => {
    expect(isGrowthFleet(makeCarrier({ power_units: 5 }))).toBe(true);
    expect(isGrowthFleet(makeCarrier({ power_units: 25 }))).toBe(true);
  });

  it("is false above the growth band", () => {
    expect(isGrowthFleet(makeCarrier({ power_units: 26 }))).toBe(false);
  });

  it("is false when power_units is missing", () => {
    expect(isGrowthFleet(makeCarrier({ power_units: null }))).toBe(false);
  });
});

describe("prospectTier", () => {
  it("classifies hot, warm, and cold tiers by lead score", () => {
    expect(prospectTier(makeCarrier({ lead_score: 60 }))).toBe("hot");
    expect(prospectTier(makeCarrier({ lead_score: 40 }))).toBe("warm");
    expect(prospectTier(makeCarrier({ lead_score: 39 }))).toBe("cold");
    expect(prospectTier(makeCarrier({ lead_score: null }))).toBe("cold");
  });
});

describe("formatFleetSize", () => {
  it("pluralizes truck count and handles missing data", () => {
    expect(formatFleetSize(1)).toBe("1 truck");
    expect(formatFleetSize(5)).toBe("5 trucks");
    expect(formatFleetSize(null)).toBe("Fleet size unknown");
  });
});
