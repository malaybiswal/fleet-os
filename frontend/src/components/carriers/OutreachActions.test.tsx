import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OutreachActions } from "./OutreachActions";
import type { CarrierListItem } from "@/types";

const { logContact, updateOutreachStatus } = vi.hoisted(() => ({
  logContact: vi.fn(),
  updateOutreachStatus: vi.fn(),
}));

vi.mock("@/lib/api", () => ({ logContact, updateOutreachStatus }));

afterEach(() => {
  cleanup();
  logContact.mockReset();
  updateOutreachStatus.mockReset();
});

const baseCarrier: CarrierListItem = {
  id: 7,
  dot_number: "1234567",
  mc_number: null,
  legal_name: "ACME Freight LLC",
  dba_name: null,
  phone: "5551234567",
  email: "ops@acme.test",
  address_line1: null,
  city: "Dallas",
  state: "TX",
  postal_code: null,
  country: "US",
  authority_status: "active",
  authority_date: null,
  power_units: 10,
  driver_count: 8,
  cargo_types: null,
  lead_score: 72,
  outreach_status: "not_contacted",
  contact_attempts: 2,
  last_contacted_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("OutreachActions", () => {
  it("renders Call and Email links when contact info exists", () => {
    render(<OutreachActions carrier={baseCarrier} onUpdated={vi.fn()} />);
    expect(screen.getByText("Call").getAttribute("href")).toBe("tel:5551234567");
    expect(screen.getByText("Email").getAttribute("href")).toBe("mailto:ops@acme.test");
  });

  it("hides Call and Email when no phone or email is on file", () => {
    render(
      <OutreachActions
        carrier={{ ...baseCarrier, phone: null, email: null }}
        onUpdated={vi.fn()}
      />,
    );
    expect(screen.queryByText("Call")).toBeNull();
    expect(screen.queryByText("Email")).toBeNull();
  });

  it("shows the contact attempts badge", () => {
    render(<OutreachActions carrier={baseCarrier} onUpdated={vi.fn()} />);
    expect(screen.getByText(/📞 2/)).toBeTruthy();
  });

  it("logs a call and reports the updated carrier", async () => {
    const updated = { ...baseCarrier, contact_attempts: 3, outreach_status: "contacted" };
    logContact.mockResolvedValue(updated);
    const onUpdated = vi.fn();

    render(<OutreachActions carrier={baseCarrier} onUpdated={onUpdated} />);
    fireEvent.click(screen.getByText("Log Call"));

    await waitFor(() => expect(logContact).toHaveBeenCalledWith(7, { method: "call" }));
    expect(onUpdated).toHaveBeenCalledWith(updated);
  });

  it("changes outreach status via the select", async () => {
    const updated = { ...baseCarrier, outreach_status: "converted" };
    updateOutreachStatus.mockResolvedValue(updated);
    const onUpdated = vi.fn();

    render(<OutreachActions carrier={baseCarrier} onUpdated={onUpdated} />);
    fireEvent.change(screen.getByLabelText("Outreach status"), {
      target: { value: "converted" },
    });

    await waitFor(() =>
      expect(updateOutreachStatus).toHaveBeenCalledWith(7, "converted"),
    );
    expect(onUpdated).toHaveBeenCalledWith(updated);
  });
});
