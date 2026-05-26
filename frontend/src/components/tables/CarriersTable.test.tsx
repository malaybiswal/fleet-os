import React from "react";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CarriersTable } from "./CarriersTable";
import type { CarrierListItem } from "@/types";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));
vi.mock("next/link", () => ({
  default: ({ href, onClick, children, className }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} onClick={onClick} className={className}>{children}</a>
  ),
}));

afterEach(() => {
  cleanup();
  mockPush.mockClear();
});

const baseCarrier: CarrierListItem = {
  id: 1,
  dot_number: "123456",
  mc_number: "MC-999",
  legal_name: "ACME Freight LLC",
  dba_name: null,
  phone: "555-1234",
  email: null,
  address_line1: null,
  city: null,
  state: "TX",
  postal_code: null,
  country: null,
  authority_status: "active",
  authority_date: null,
  power_units: 10,
  driver_count: 8,
  cargo_types: ["General Freight"],
  lead_score: 92,
  outreach_status: "not_contacted",
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const defaultProps = {
  carriers: [baseCarrier],
  total: 1,
  page: 1,
  totalPages: 1,
  onPageChange: vi.fn(),
};

describe("CarriersTable", () => {
  it("renders a row for each carrier with key fields", () => {
    render(<CarriersTable {...defaultProps} />);
    expect(screen.getByText("ACME Freight LLC")).toBeTruthy();
    expect(screen.getByText("123456")).toBeTruthy();
    expect(screen.getByText("MC-999")).toBeTruthy();
    expect(screen.getByText("TX")).toBeTruthy();
    expect(screen.getByText("92")).toBeTruthy();
  });

  it("shows empty state when carriers array is empty", () => {
    render(<CarriersTable {...defaultProps} carriers={[]} total={0} />);
    expect(screen.getByText("No carriers found")).toBeTruthy();
  });

  it("navigates to /carriers/[id] when a row is clicked", () => {
    render(<CarriersTable {...defaultProps} />);
    fireEvent.click(screen.getByText("ACME Freight LLC"));
    expect(mockPush).toHaveBeenCalledWith("/carriers/1");
  });

  it("phone link click does not trigger row navigation", () => {
    render(<CarriersTable {...defaultProps} />);
    fireEvent.click(screen.getByText("555-1234"));
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("disables Prev button on the first page", () => {
    render(<CarriersTable {...defaultProps} page={1} totalPages={3} total={3} />);
    const prev = screen.getByText("← Prev");
    expect((prev as HTMLButtonElement).disabled).toBe(true);
  });

  it("disables Next button on the last page", () => {
    render(<CarriersTable {...defaultProps} page={3} totalPages={3} total={3} />);
    const next = screen.getByText("Next →");
    expect((next as HTMLButtonElement).disabled).toBe(true);
  });

  it("both Prev and Next are enabled on a middle page", () => {
    render(<CarriersTable {...defaultProps} page={2} totalPages={3} total={3} />);
    expect((screen.getByText("← Prev") as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByText("Next →") as HTMLButtonElement).disabled).toBe(false);
  });

  it("shows singular 'carrier' for total of 1", () => {
    render(<CarriersTable {...defaultProps} total={1} />);
    expect(screen.getByText((t) => t === "1 carrier")).toBeTruthy();
  });

  it("shows plural 'carriers' for total greater than 1", () => {
    render(<CarriersTable {...defaultProps} total={42} />);
    expect(screen.getByText(/42 carriers/)).toBeTruthy();
  });

  it("formats authority age in days when under 365 days", () => {
    const carrier = {
      ...baseCarrier,
      authority_date: new Date(Date.now() - 90 * 86_400_000).toISOString(),
    };
    render(<CarriersTable {...defaultProps} carriers={[carrier]} />);
    expect(screen.getByText("90d")).toBeTruthy();
  });

  it("formats authority age in years when 365 days or more", () => {
    const carrier = {
      ...baseCarrier,
      authority_date: new Date(Date.now() - 730 * 86_400_000).toISOString(),
    };
    render(<CarriersTable {...defaultProps} carriers={[carrier]} />);
    expect(screen.getByText("2.0y")).toBeTruthy();
  });

  it("shows — for authority age when authority_date is null", () => {
    render(<CarriersTable {...defaultProps} carriers={[{ ...baseCarrier, authority_date: null }]} />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});
