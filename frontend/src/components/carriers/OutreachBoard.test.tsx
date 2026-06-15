import React from "react";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OutreachBoard, moveCarrierBetweenColumns, type Columns } from "./OutreachBoard";
import type { CarrierListItem } from "@/types";

const { listCarriers, updateOutreachStatus } = vi.hoisted(() => ({
  listCarriers: vi.fn(),
  updateOutreachStatus: vi.fn(),
}));

vi.mock("@/lib/api", () => ({ listCarriers, updateOutreachStatus }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

afterEach(() => {
  cleanup();
  listCarriers.mockReset();
  updateOutreachStatus.mockReset();
});

function carrier(id: number, status: string, name: string): CarrierListItem {
  return {
    id,
    dot_number: `DOT-${id}`,
    mc_number: null,
    legal_name: name,
    dba_name: null,
    phone: null,
    email: null,
    address_line1: null,
    city: "Dallas",
    state: "TX",
    postal_code: null,
    country: "US",
    authority_status: "active",
    authority_date: null,
    power_units: 5,
    driver_count: 4,
    cargo_types: null,
    lead_score: 50,
    outreach_status: status,
    contact_attempts: 0,
    last_contacted_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

describe("moveCarrierBetweenColumns", () => {
  const cols = (): Columns => ({
    not_contacted: [carrier(1, "not_contacted", "A")],
    contacted: [],
    follow_up: [],
    not_interested: [],
    converted: [],
  });

  it("moves a carrier to the target column and updates its status", () => {
    const next = moveCarrierBetweenColumns(cols(), 1, "not_contacted", "contacted");
    expect(next.not_contacted).toHaveLength(0);
    expect(next.contacted).toHaveLength(1);
    expect(next.contacted[0].outreach_status).toBe("contacted");
  });

  it("is a no-op when source equals target", () => {
    const start = cols();
    expect(moveCarrierBetweenColumns(start, 1, "not_contacted", "not_contacted")).toBe(
      start,
    );
  });

  it("does not mutate the input columns", () => {
    const start = cols();
    moveCarrierBetweenColumns(start, 1, "not_contacted", "contacted");
    expect(start.not_contacted).toHaveLength(1);
  });
});

describe("OutreachBoard", () => {
  it("groups fetched carriers into their status columns", async () => {
    listCarriers.mockImplementation(({ outreach_status }: { outreach_status: string }) => {
      const data =
        outreach_status === "not_contacted"
          ? [carrier(1, "not_contacted", "Cold Carrier")]
          : outreach_status === "converted"
            ? [carrier(2, "converted", "Won Carrier")]
            : [];
      return Promise.resolve({ data });
    });

    render(<OutreachBoard />);

    await waitFor(() => {
      const notContacted = screen.getByTestId("column-not_contacted");
      expect(within(notContacted).getByText("Cold Carrier")).toBeTruthy();
    });
    const converted = screen.getByTestId("column-converted");
    expect(within(converted).getByText("Won Carrier")).toBeTruthy();
  });
});
